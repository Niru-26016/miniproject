// ===== DOM REFERENCES =====
const searchForm = document.getElementById('searchForm');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const loadingSection = document.getElementById('loadingSection');
const loadingQuery = document.getElementById('loadingQuery');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const dashboard = document.getElementById('dashboard');

// Chart instances
let pieChart = null;
let barChart = null;
let donutChart = null;

// Current data (for filtering)
let currentPosts = [];

// ===== CHART.JS DEFAULTS =====
Chart.defaults.color = '#8b8b9e';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;

// ===== SEARCH HANDLER =====
searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (!query) return;
    await performSearch(query);
});

function quickSearch(query) {
    searchInput.value = query;
    performSearch(query);
}

async function performSearch(query) {
    showLoading(query);

    // Animate loading steps
    const steps = ['step1', 'step2', 'step3', 'step4'];
    let stepIndex = 0;
    const stepTimer = setInterval(() => {
        if (stepIndex > 0) {
            document.getElementById(steps[stepIndex - 1]).classList.remove('active');
            document.getElementById(steps[stepIndex - 1]).classList.add('done');
        }
        if (stepIndex < steps.length) {
            document.getElementById(steps[stepIndex]).classList.add('active');
            stepIndex++;
        } else {
            clearInterval(stepTimer);
        }
    }, 2000);

    try {
        const response = await fetch(`/api/analyze/${encodeURIComponent(query)}`);
        const data = await response.json();

        clearInterval(stepTimer);

        if (data.error) {
            showError(data.error);
            return;
        }

        renderDashboard(data);
    } catch (err) {
        clearInterval(stepTimer);
        showError('Failed to connect to the server. Make sure the backend is running.');
        console.error(err);
    }
}

// ===== UI STATE MANAGEMENT =====
function showLoading(query) {
    loadingQuery.textContent = query;
    loadingSection.style.display = '';
    errorSection.style.display = 'none';
    dashboard.style.display = 'none';

    // Reset all steps
    document.querySelectorAll('.loader-step').forEach(s => {
        s.classList.remove('active', 'done');
    });
    document.getElementById('step1').classList.add('active');
}

function showError(msg) {
    loadingSection.style.display = 'none';
    errorSection.style.display = '';
    dashboard.style.display = 'none';
    errorMessage.textContent = msg;
}

function showDashboard() {
    loadingSection.style.display = 'none';
    errorSection.style.display = 'none';
    dashboard.style.display = '';
}

// ===== RENDER DASHBOARD =====
function renderDashboard(data) {
    showDashboard();

    // Query label & timestamp
    document.getElementById('queryLabel').textContent = data.query;
    document.getElementById('timestamp').textContent = new Date().toLocaleString();

    // Stats
    animateCounter('totalPosts', data.total_posts);
    animateCounter('positiveCount', data.sentiment_summary.positive);
    animateCounter('negativeCount', data.sentiment_summary.negative);
    animateCounter('fakeCount', data.fake_posts_detected);

    const avgEl = document.getElementById('avgSentiment');
    avgEl.textContent = data.avg_sentiment > 0 ? `+${data.avg_sentiment}` : data.avg_sentiment;
    avgEl.style.color = data.avg_sentiment >= 0.05 ? '#22c55e' : data.avg_sentiment <= -0.05 ? '#ef4444' : '#eab308';

    // Charts
    renderPieChart(data.sentiment_summary);
    renderBarChart(data.posts);
    renderDonutChart(data.total_posts - data.fake_posts_detected, data.fake_posts_detected);

    // AI Insight
    document.getElementById('aiInsight').innerHTML = formatInsight(data.ai_insight);

    // Posts table
    currentPosts = data.posts;
    renderPostsTable(currentPosts);

    // Scroll to dashboard
    dashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ===== COUNTER ANIMATION =====
function animateCounter(id, target) {
    const el = document.getElementById(id);
    const duration = 800;
    const start = performance.now();
    const from = 0;

    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(from + (target - from) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ===== CHARTS =====
function renderPieChart(summary) {
    const ctx = document.getElementById('sentimentPieChart').getContext('2d');
    if (pieChart) pieChart.destroy();

    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [summary.positive, summary.negative, summary.neutral],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.85)',
                    'rgba(239, 68, 68, 0.85)',
                    'rgba(234, 179, 8, 0.85)'
                ],
                borderColor: 'transparent',
                borderWidth: 0,
                hoverOffset: 8,
                spacing: 3,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20, font: { size: 13 } }
                }
            }
        }
    });
}

function renderBarChart(posts) {
    const ctx = document.getElementById('sentimentBarChart').getContext('2d');
    if (barChart) barChart.destroy();

    const labels = posts.map((_, i) => `#${i + 1}`);
    const scores = posts.map(c => c.sentiment_score);
    const colors = scores.map(s =>
        s >= 0.05 ? 'rgba(34, 197, 94, 0.7)' :
            s <= -0.05 ? 'rgba(239, 68, 68, 0.7)' :
                'rgba(234, 179, 8, 0.7)'
    );

    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Sentiment Score',
                data: scores,
                backgroundColor: colors,
                borderRadius: 4,
                borderSkipped: false,
                barPercentage: 0.7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: -1,
                    max: 1,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { font: { size: 11 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: (ctx) => {
                            const c = posts[ctx.dataIndex];
                            return `${c.content.substring(0, 80)}...`;
                        }
                    }
                }
            }
        }
    });
}

function renderDonutChart(realCount, fakeCount) {
    const ctx = document.getElementById('fakeDonutChart').getContext('2d');
    if (donutChart) donutChart.destroy();

    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Real Posts', 'Fake Posts'],
            datasets: [{
                data: [realCount, fakeCount],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.85)',
                    'rgba(239, 68, 68, 0.85)'
                ],
                borderColor: 'transparent',
                borderWidth: 0,
                hoverOffset: 8,
                spacing: 3,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20, font: { size: 13 } }
                }
            }
        }
    });
}

// ===== FORMAT INSIGHT =====
function formatInsight(text) {
    if (!text) return '<p>No insight available.</p>';
    // Convert markdown bold
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    return `<p>${html}</p>`;
}

// ===== POSTS TABLE =====
function renderPostsTable(posts) {
    const tbody = document.getElementById('postsBody');
    tbody.innerHTML = '';

    posts.forEach((c, i) => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-sentiment', c.sentiment_label);
        tr.setAttribute('data-authenticity', c.is_fake ? 'fake' : 'real');

        // Score bar color
        const normalized = (c.sentiment_score + 1) / 2; // -1..1 → 0..1
        const barColor = c.sentiment_score >= 0.05 ? '#22c55e' :
            c.sentiment_score <= -0.05 ? '#ef4444' : '#eab308';

        // Fake confidence bar color
        const fakeBarColor = c.is_fake ? '#ef4444' : '#22c55e';

        tr.innerHTML = `
            <td style="color: var(--text-muted); font-weight: 500;">${i + 1}</td>
            <td><span class="author-name">${escapeHtml(c.author || 'Unknown')}</span></td>
            <td title="${escapeHtml(c.content)}">${escapeHtml(truncate(c.content, 100))}</td>
            <td><span class="badge badge-${c.sentiment_label}">${c.sentiment_label}</span></td>
            <td>
                <div class="score-bar">
                    <span style="font-weight:600; font-size:0.82rem;">${c.sentiment_score}</span>
                    <div class="score-bar-track">
                        <div class="score-bar-fill" style="width:${normalized * 100}%; background:${barColor};"></div>
                    </div>
                </div>
            </td>
            <td><span class="badge ${c.is_fake ? 'badge-fake' : 'badge-real'}">${c.is_fake ? '⚠ Fake' : '✓ Real'}</span></td>
            <td>
                <div class="score-bar">
                    <span style="font-weight:600; font-size:0.82rem;">${(c.fake_confidence * 100).toFixed(0)}%</span>
                    <div class="score-bar-track">
                        <div class="score-bar-fill" style="width:${c.fake_confidence * 100}%; background:${fakeBarColor};"></div>
                    </div>
                </div>
            </td>
            <td>
                <a href="${c.url}" target="_blank" rel="noopener" class="link-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        <polyline points="15 3 21 3 21 9"/>
                        <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                </a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// ===== TABLE FILTER =====
function filterPosts(filter, btnEl) {
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btnEl.classList.add('active');

    const rows = document.querySelectorAll('#postsBody tr');
    rows.forEach(row => {
        const sentiment = row.getAttribute('data-sentiment');
        const authenticity = row.getAttribute('data-authenticity');

        if (filter === 'all') {
            row.style.display = '';
        } else if (filter === 'real' || filter === 'fake') {
            row.style.display = authenticity === filter ? '' : 'none';
        } else {
            row.style.display = sentiment === filter ? '' : 'none';
        }
    });
}

// ===== UTILITIES =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, maxLen) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}
