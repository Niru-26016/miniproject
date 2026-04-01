// ===== Brand Insight Engine — Dashboard JS =====

let chartInstances = {};
let lastQuery = '';
let autoRefreshInterval = null;
let countdownInterval = null;
let countdownSeconds = 30;

// ===== PARTICLES BACKGROUND =====
function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    for (let i = 0; i < 30; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.cssText = `
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            width: ${Math.random() * 4 + 1}px;
            height: ${Math.random() * 4 + 1}px;
            animation-delay: ${Math.random() * 6}s;
            animation-duration: ${Math.random() * 10 + 10}s;
        `;
        container.appendChild(p);
    }
}
createParticles();

// ===== SEARCH =====
document.getElementById('searchForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const query = document.getElementById('searchInput').value.trim();
    if (!query) return;
    lastQuery = query;
    runAnalysis(query);
});

function quickSearch(term) {
    document.getElementById('searchInput').value = term;
    lastQuery = term;
    runAnalysis(term);
}

// ===== LOADING ANIMATION =====
function showLoading(query) {
    document.getElementById('loadingSection').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.getElementById('loadingQuery').textContent = query;

    const steps = ['step1','step2','step3','step4','step5'];
    steps.forEach(s => document.getElementById(s).classList.remove('active','done'));
    document.getElementById('step1').classList.add('active');

    let idx = 0;
    const interval = setInterval(() => {
        if (idx < steps.length) {
            document.getElementById(steps[idx]).classList.remove('active');
            document.getElementById(steps[idx]).classList.add('done');
        }
        idx++;
        if (idx < steps.length) {
            document.getElementById(steps[idx]).classList.add('active');
        } else {
            clearInterval(interval);
        }
    }, 2500);
    return interval;
}

// ===== MAIN ANALYSIS =====
async function runAnalysis(query) {
    const loadingInterval = showLoading(query);
    const btn = document.getElementById('searchBtn');
    btn.disabled = true;
    btn.querySelector('.btn-text').textContent = 'Analyzing...';

    try {
        const res = await fetch(`/api/analyze/${encodeURIComponent(query)}`);
        const data = await res.json();

        clearInterval(loadingInterval);
        document.getElementById('loadingSection').style.display = 'none';

        if (data.error) {
            document.getElementById('errorSection').style.display = 'flex';
            document.getElementById('errorMessage').textContent = data.error;
            return;
        }

        renderDashboard(data);
    } catch (err) {
        clearInterval(loadingInterval);
        document.getElementById('loadingSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'flex';
        document.getElementById('errorMessage').textContent = `Network error: ${err.message}`;
    } finally {
        btn.disabled = false;
        btn.querySelector('.btn-text').textContent = 'Analyze';
    }
}

// ===== RENDER DASHBOARD =====
function renderDashboard(data) {
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('queryLabel').textContent = data.query;
    document.getElementById('timestamp').textContent = new Date().toLocaleString();

    // Stats
    animateCounter('totalPosts', data.total_posts);
    animateCounter('positiveCount', data.sentiment_summary.positive);
    animateCounter('negativeCount', data.sentiment_summary.negative);
    animateCounter('fakeCount', data.fake_posts_detected);
    animateCounter('avgTrust', data.avg_trust_score || 0);

    const avgEl = document.getElementById('avgSentiment');
    avgEl.textContent = data.avg_sentiment > 0 ? `+${data.avg_sentiment}` : data.avg_sentiment;
    avgEl.className = `stat-value ${data.avg_sentiment >= 0.05 ? 'text-green' : data.avg_sentiment <= -0.05 ? 'text-red' : ''}`;

    // Scroll to dashboard
    document.getElementById('dashboard').scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Charts
    renderSentimentPie(data.sentiment_summary);
    renderSentimentBar(data.posts);
    renderFakeDonut(data);
    renderEmotionChart(data.emotions || {});
    renderAspectChart(data.aspects || []);

    // Keywords
    renderKeywords(data.keywords || []);

    // AI Insight
    document.getElementById('aiInsight').innerHTML = formatInsight(data.ai_insight);

    // Recommendations
    renderRecommendations(data.recommendations || []);

    // Posts Table
    renderPostsTable(data.posts);
}

// ===== COUNTER ANIMATION =====
function animateCounter(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 30));
    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = current;
    }, 30);
}

// ===== CHARTS =====
function destroyChart(key) {
    if (chartInstances[key]) { chartInstances[key].destroy(); }
}

function renderSentimentPie(summary) {
    destroyChart('pie');
    const ctx = document.getElementById('sentimentPieChart').getContext('2d');
    chartInstances.pie = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [summary.positive, summary.negative, summary.neutral || 0],
                backgroundColor: ['#22c55e', '#ef4444', '#64748b'],
                borderWidth: 0,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' } } } }
        }
    });
}

function renderSentimentBar(posts) {
    destroyChart('bar');
    const ctx = document.getElementById('sentimentBarChart').getContext('2d');
    const labels = posts.map((_, i) => `#${i+1}`);
    const scores = posts.map(p => p.sentiment_score);
    const colors = scores.map(s => s >= 0.05 ? '#22c55e' : s <= -0.05 ? '#ef4444' : '#64748b');

    chartInstances.bar = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Sentiment Score',
                data: scores,
                backgroundColor: colors,
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: -1, max: 1, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderFakeDonut(data) {
    destroyChart('fake');
    const ctx = document.getElementById('fakeDonutChart').getContext('2d');
    const real = data.total_posts - data.fake_posts_detected - (data.bot_flagged_count || 0);
    chartInstances.fake = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Real Posts', 'Fake Detected', 'Bot Flagged'],
            datasets: [{
                data: [Math.max(0, real), data.fake_posts_detected, data.bot_flagged_count || 0],
                backgroundColor: ['#22c55e', '#ef4444', '#f97316'],
                borderWidth: 0,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' } } } }
        }
    });
}

function renderEmotionChart(emotions) {
    destroyChart('emotion');
    const ctx = document.getElementById('emotionChart').getContext('2d');
    const emotionLabels = ['Joy', 'Anger', 'Fear', 'Surprise', 'Sadness', 'Disgust', 'Neutral'];
    const emotionKeys = ['joy', 'anger', 'fear', 'surprise', 'sadness', 'disgust', 'neutral'];
    const emotionColors = ['#22c55e', '#ef4444', '#a855f7', '#eab308', '#3b82f6', '#f97316', '#64748b'];
    const emotionData = emotionKeys.map(k => emotions[k] || 0);

    chartInstances.emotion = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: emotionLabels,
            datasets: [{
                label: 'Emotion Detection',
                data: emotionData,
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                borderColor: '#6366f1',
                borderWidth: 2,
                pointBackgroundColor: emotionColors,
                pointBorderColor: '#fff',
                pointBorderWidth: 1,
                pointRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    grid: { color: 'rgba(148,163,184,0.15)' },
                    angleLines: { color: 'rgba(148,163,184,0.15)' },
                    pointLabels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } },
                    ticks: { display: false }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderAspectChart(aspects) {
    destroyChart('aspect');
    const ctx = document.getElementById('aspectChart').getContext('2d');

    if (!aspects.length) {
        chartInstances.aspect = new Chart(ctx, {
            type: 'bar',
            data: { labels: ['No aspects detected'], datasets: [{ data: [0], backgroundColor: ['#64748b'], borderRadius: 6 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
        });
        return;
    }

    const labels = aspects.map(a => a.aspect);
    const mentions = aspects.map(a => a.mentions || 1);
    const colors = aspects.map(a => {
        if (a.sentiment === 'positive') return '#22c55e';
        if (a.sentiment === 'negative') return '#ef4444';
        return '#64748b';
    });

    chartInstances.aspect = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Mentions',
                data: mentions,
                backgroundColor: colors,
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#94a3b8' } },
                y: { grid: { display: false }, ticks: { color: '#e2e8f0', font: { family: 'Inter', weight: 600 } } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// ===== KEYWORDS =====
function renderKeywords(keywords) {
    const container = document.getElementById('keywordsContainer');
    if (!keywords.length) {
        container.innerHTML = '<p class="no-data">No keywords extracted</p>';
        return;
    }
    container.innerHTML = keywords.map(k => `
        <div class="keyword-pill">
            <span class="keyword-name">${k.keyword}</span>
            <span class="keyword-meta">${k.mentions || 0} mentions · ${((k.relevance || 0) * 100).toFixed(0)}%</span>
        </div>
    `).join('');
}

// ===== RECOMMENDATIONS =====
function renderRecommendations(recs) {
    const grid = document.getElementById('recommendationsGrid');
    if (!recs.length) {
        grid.innerHTML = '<p class="no-data">No recommendations generated</p>';
        return;
    }
    grid.innerHTML = recs.map(r => {
        const priorityClass = r.priority === 'high' ? 'priority-high' : r.priority === 'medium' ? 'priority-medium' : 'priority-low';
        const priorityIcon = r.priority === 'high' ? '🔴' : r.priority === 'medium' ? '🟡' : '🟢';
        return `
        <div class="rec-card ${priorityClass}">
            <div class="rec-header">
                <span class="rec-priority">${priorityIcon} ${r.priority.toUpperCase()}</span>
            </div>
            <h4 class="rec-title">${r.title}</h4>
            <p class="rec-desc">${r.description}</p>
        </div>
        `;
    }).join('');
}

// ===== FORMAT INSIGHT =====
function formatInsight(text) {
    if (!text) return '<p>No insight available.</p>';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.*$)/gm, '<h4>$1</h4>')
        .replace(/^## (.*$)/gm, '<h3>$1</h3>')
        .replace(/^- (.*$)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
        .replace(/\n{2,}/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^(.+)$/gm, (match) => {
            if (match.startsWith('<')) return match;
            return match;
        });
}

// ===== POSTS TABLE =====
function renderPostsTable(posts) {
    const tbody = document.getElementById('postsBody');
    tbody.innerHTML = '';

    posts.forEach((c, i) => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-sentiment', c.sentiment_label);
        tr.setAttribute('data-authenticity', c.is_fake ? 'fake' : 'real');
        tr.setAttribute('data-bot', (c.bot_score || 0) >= 0.35 ? 'yes' : 'no');

        // Sentiment bar color
        const normalized = (c.sentiment_score + 1) / 2;
        const barColor = c.sentiment_score >= 0.05 ? '#22c55e' : c.sentiment_score <= -0.05 ? '#ef4444' : '#64748b';

        // Trust badge
        const trustScore = c.trust_score || 0;
        const trustColor = trustScore >= 70 ? '#22c55e' : trustScore >= 40 ? '#eab308' : '#ef4444';

        // Credibility badge
        const credLevel = c.credibility_level || 'medium';
        const credScore = c.credibility_score || 50;
        const credColor = credLevel === 'high' ? '#22c55e' : credLevel === 'medium' ? '#eab308' : '#ef4444';

        // Emotion emoji
        const emotionEmojis = {
            joy: '😊', anger: '😠', fear: '😨', surprise: '😲',
            sadness: '😢', disgust: '🤢', neutral: '😐'
        };
        const emotionEmoji = emotionEmojis[c.emotion || 'neutral'] || '😐';
        const emotionLabel = (c.emotion || 'neutral').charAt(0).toUpperCase() + (c.emotion || 'neutral').slice(1);

        // Fake label
        const fakeLabel = c.is_fake
            ? `<span class="badge badge-fake">FAKE</span>`
            : `<span class="badge badge-real">REAL</span>`;

        tr.innerHTML = `
            <td>${i + 1}</td>
            <td>
                <div class="author-cell">
                    <span class="author-name">${c.author || 'Unknown'}</span>
                    <span class="author-sub">r/${c.subreddit || '?'}</span>
                </div>
            </td>
            <td>
                <div class="post-content">${c.content ? c.content.substring(0, 120) + (c.content.length > 120 ? '...' : '') : 'N/A'}</div>
            </td>
            <td>
                <span class="emotion-badge">${emotionEmoji} ${emotionLabel}</span>
            </td>
            <td>
                <div class="score-bar">
                    <span class="sentiment-label label-${c.sentiment_label}">${c.sentiment_label}</span>
                    <div class="score-bar-track">
                        <div class="score-bar-fill" style="width:${normalized * 100}%; background:${barColor};"></div>
                    </div>
                </div>
            </td>
            <td class="score-cell">${c.score || 0} ▲</td>
            <td>
                <div class="trust-badge" style="--trust-color: ${trustColor}">
                    <span class="trust-value">${trustScore}</span>
                    <svg width="28" height="28" viewBox="0 0 36 36" class="trust-ring">
                        <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="3"/>
                        <circle cx="18" cy="18" r="15" fill="none" stroke="${trustColor}" stroke-width="3"
                                stroke-dasharray="${trustScore * 0.94} 94" stroke-linecap="round"
                                transform="rotate(-90 18 18)"/>
                    </svg>
                </div>
            </td>
            <td>
                <span class="cred-badge cred-${credLevel}" title="Credibility: ${credScore}/100">
                    ${credLevel.toUpperCase()}
                </span>
            </td>
            <td>${fakeLabel}</td>
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

// ===== FILTER POSTS =====
function filterPosts(filter, btn) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const rows = document.querySelectorAll('#postsBody tr');
    rows.forEach(row => {
        const sentiment = row.getAttribute('data-sentiment');
        const authenticity = row.getAttribute('data-authenticity');
        const isBot = row.getAttribute('data-bot');

        if (filter === 'all') {
            row.style.display = '';
        } else if (filter === 'real' || filter === 'fake') {
            row.style.display = authenticity === filter ? '' : 'none';
        } else if (filter === 'bot') {
            row.style.display = isBot === 'yes' ? '' : 'none';
        } else {
            row.style.display = sentiment === filter ? '' : 'none';
        }
    });
}

// ===== AUTO-REFRESH / LIVE DASHBOARD =====
document.getElementById('autoRefreshToggle').addEventListener('change', function() {
    const countdownEl = document.getElementById('refreshCountdown');
    if (this.checked && lastQuery) {
        countdownSeconds = 30;
        countdownEl.textContent = `(${countdownSeconds}s)`;

        countdownInterval = setInterval(() => {
            countdownSeconds--;
            countdownEl.textContent = `(${countdownSeconds}s)`;
            if (countdownSeconds <= 0) {
                countdownSeconds = 30;
            }
        }, 1000);

        autoRefreshInterval = setInterval(() => {
            runAnalysis(lastQuery);
        }, 30000);
    } else {
        clearInterval(autoRefreshInterval);
        clearInterval(countdownInterval);
        autoRefreshInterval = null;
        countdownEl.textContent = '';
    }
});
