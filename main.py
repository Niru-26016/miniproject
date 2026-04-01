import os, uuid, chromadb
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from core.scraper import RedditScraper
from core.bot_shield import BotShield
from core.nlp_engine import NLPEngine
from dotenv import load_dotenv
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Brand Insight Engine")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

reddit = RedditScraper()
shield = BotShield()
brain = NLPEngine(api_key=OPENAI_KEY)
vader = SentimentIntensityAnalyzer()

# Vector DB
chroma_client = chromadb.PersistentClient(path="./brand_db")
collection = chroma_client.get_or_create_collection(name="human_feedback")

# ---------- Credibility Score ----------

def calculate_credibility(post: dict) -> dict:
    """
    Calculate a 0-100 credibility score from Reddit metadata.
    Returns: { score: int, level: str }
    """
    score = 50  # Start at 50/100

    # Author premium (+15)
    if post.get('author_premium'):
        score += 15

    # Author flair (+10)
    if post.get('author_flair_text'):
        score += 10

    # Upvote ratio
    ratio = post.get('upvote_ratio')
    if ratio is not None:
        if ratio >= 0.9:
            score += 15
        elif ratio >= 0.7:
            score += 8
        elif ratio < 0.4:
            score -= 15

    # Post score (karma)
    post_score = post.get('score', 0)
    if post_score > 500:
        score += 12
    elif post_score > 100:
        score += 8
    elif post_score > 10:
        score += 3
    elif post_score < 0:
        score -= 15

    # Awards
    if post.get('total_awards', 0) >= 1:
        score += 10

    # Comment engagement
    comments = post.get('comment_count', 0)
    if comments > 100:
        score += 10
    elif comments > 20:
        score += 5
    elif comments == 0:
        score -= 10

    # Subreddit size (large = more moderated)
    sub_size = post.get('subreddit_subscribers', 0)
    if sub_size > 1000000:
        score += 8
    elif sub_size > 100000:
        score += 4
    elif sub_size < 1000:
        score -= 8

    # Suspicious author
    author = post.get('author', '')
    if not author or author in ('[deleted]', '[removed]'):
        score -= 20

    # Clamp 0-100
    score = max(0, min(100, score))

    # Level
    if score >= 75:
        level = 'high'
    elif score >= 45:
        level = 'medium'
    else:
        level = 'low'

    return {"score": score, "level": level}


# ---------- Trust Score ----------

def calculate_trust_score(bot_score: float, fake_confidence: float, is_fake: bool) -> int:
    """
    Combine BotShield + fake detection into a single 0-100 trust score.
    Higher = more trustworthy.
    """
    # Start at 100, subtract based on bot/fake signals
    trust = 100.0

    # BotShield contribution (0-40 points penalty)
    trust -= bot_score * 40

    # Fake detection contribution (0-50 points penalty)
    trust -= fake_confidence * 50

    # Hard penalty if classified fake
    if is_fake:
        trust -= 20

    return max(0, min(100, round(trust)))


# ---------- Sync Endpoint ----------

@app.post("/api/sync/{brand}")
async def sync_data(brand: str, background_tasks: BackgroundTasks):
    def run():
        posts = reddit.scrape(brand)
        for p in posts:
            result = shield.analyze(p)
            if not result['is_bot']:
                collection.add(
                    documents=[p['content']],
                    metadatas=[{"brand": brand.lower(), "author": p['author']}],
                    ids=[f"{brand}_{p['id']}"]
                )
    background_tasks.add_task(run)
    return {"message": f"Syncing {brand} data and filtering bots..."}

@app.get("/api/report/{brand}")
async def get_report(brand: str):
    results = collection.query(query_texts=["complaints"], n_results=10, where={"brand": brand.lower()})
    if not results['documents'][0]: return {"error": "No human data found."}
    insight = brain.generate_insight(brand, "\n".join(results['documents'][0]))
    return {"brand": brand, "ai_report": insight}

# ---------- Dashboard Endpoint ----------

@app.get("/api/analyze/{query}")
async def analyze_product(query: str):
    """
    Full analysis pipeline:
    1. Scrape Reddit
    2. VADER sentiment
    3. BotShield heuristic analysis
    4. OpenAI fake detection
    5. Credibility & Trust scores
    6. Advanced AI analysis (emotions, aspects, keywords, recommendations)
    7. AI insight summary
    """
    # Step 1: Scrape
    posts = reddit.scrape(query)
    if not posts:
        return {"error": "No results found. Try a different search term.", "query": query}

    # Step 2: VADER sentiment
    for p in posts:
        scores = vader.polarity_scores(p['content'])
        p['sentiment_score'] = round(scores['compound'], 3)
        if scores['compound'] >= 0.05:
            p['sentiment_label'] = 'positive'
        elif scores['compound'] <= -0.05:
            p['sentiment_label'] = 'negative'
        else:
            p['sentiment_label'] = 'neutral'

    # Step 3: BotShield
    for p in posts:
        result = shield.analyze(p)
        p['bot_score'] = result['bot_score']
        p['bot_flags'] = result['flags']

    # Step 4: OpenAI fake detection
    post_texts = [p['content'] for p in posts]
    fake_results = brain.detect_fake_posts(post_texts)
    for i, p in enumerate(posts):
        p['is_fake'] = fake_results[i]['is_fake']
        p['fake_confidence'] = round(fake_results[i]['confidence'], 3)

    # Step 5: Credibility & Trust scores
    for p in posts:
        cred = calculate_credibility(p)
        p['credibility_score'] = cred['score']
        p['credibility_level'] = cred['level']
        p['trust_score'] = calculate_trust_score(
            p['bot_score'], p['fake_confidence'], p['is_fake']
        )

    # Step 6: Advanced AI analysis (single call for all features)
    real_texts = [p['content'] for p in posts if not p['is_fake']]
    advanced = brain.advanced_analysis(query, real_texts)

    # Attach per-post emotions
    emotion_map = {e['index']: e['emotion'] for e in advanced.get('post_emotions', [])}
    real_idx = 0
    for p in posts:
        if not p['is_fake']:
            real_idx += 1
            p['emotion'] = emotion_map.get(real_idx, 'neutral')
        else:
            p['emotion'] = 'neutral'

    # Step 7: AI insight (non-fake posts only)
    all_content = "\n".join(real_texts[:3000])
    ai_insight = brain.generate_insight(query, all_content[:3000])

    # Build summary stats
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    total_sentiment = 0
    real_count = 0
    fake_count = 0
    bot_flagged_count = 0
    total_trust = 0
    total_credibility = 0

    for p in posts:
        if p['is_fake']:
            fake_count += 1
        else:
            sentiment_counts[p['sentiment_label']] += 1
            total_sentiment += p['sentiment_score']
            real_count += 1
        if p['bot_score'] >= 0.35:
            bot_flagged_count += 1
        total_trust += p['trust_score']
        total_credibility += p['credibility_score']

    avg_sentiment = round(total_sentiment / real_count, 3) if real_count else 0
    avg_trust = round(total_trust / len(posts)) if posts else 0
    avg_credibility = round(total_credibility / len(posts)) if posts else 0

    return {
        "query": query,
        "total_posts": len(posts),
        "sentiment_summary": sentiment_counts,
        "avg_sentiment": avg_sentiment,
        "fake_posts_detected": fake_count,
        "bot_flagged_count": bot_flagged_count,
        "avg_trust_score": avg_trust,
        "avg_credibility_score": avg_credibility,
        "ai_insight": ai_insight,
        # Advanced analysis
        "emotions": advanced.get("emotions", {}),
        "aspects": advanced.get("aspects", []),
        "keywords": advanced.get("keywords", []),
        "recommendations": advanced.get("recommendations", []),
        # Posts
        "posts": posts
    }

# ---------- Serve Frontend ----------

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(static_dir, "index.html"))