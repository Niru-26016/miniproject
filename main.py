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

# Vector DB initialization
chroma_client = chromadb.PersistentClient(path="./brand_db")
collection = chroma_client.get_or_create_collection(name="human_feedback")

# ---------- Original Endpoints ----------

@app.post("/api/sync/{brand}")
async def sync_data(brand: str, background_tasks: BackgroundTasks):
    def run():
        posts = reddit.scrape(brand)
        for p in posts:
            is_bot, _ = shield.predict(p)
            if not is_bot:
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

# ---------- New Dashboard Endpoint ----------

@app.get("/api/analyze/{query}")
async def analyze_product(query: str):
    """
    Full analysis pipeline:
    1. Scrape Reddit for the query
    2. Run VADER sentiment on each comment
    3. Run BotShield on each comment
    4. Use OpenAI to detect fake/real comments
    5. Generate AI insight summary
    """
    # Step 1: Scrape
    posts = reddit.scrape(query)
    if not posts:
        return {"error": "No results found. Try a different search term.", "query": query}

    # Step 2: VADER sentiment analysis
    for p in posts:
        scores = vader.polarity_scores(p['content'])
        p['sentiment_score'] = round(scores['compound'], 3)
        if scores['compound'] >= 0.05:
            p['sentiment_label'] = 'positive'
        elif scores['compound'] <= -0.05:
            p['sentiment_label'] = 'negative'
        else:
            p['sentiment_label'] = 'neutral'

    # Step 3: Bot shield scores
    for p in posts:
        _, bot_score = shield.predict(p)
        p['bot_score'] = round(bot_score, 3)

    # Step 4: OpenAI fake comment detection
    comment_texts = [p['content'] for p in posts]
    fake_results = brain.detect_fake_comments(comment_texts)
    for i, p in enumerate(posts):
        p['is_fake'] = fake_results[i]['is_fake']
        p['fake_confidence'] = round(fake_results[i]['confidence'], 3)

    # Step 5: AI insight
    all_content = "\n".join([p['content'] for p in posts if not p['is_fake']])
    ai_insight = brain.generate_insight(query, all_content[:3000])

    # Build summary stats (exclude fake comments from sentiment)
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    total_sentiment = 0
    real_count = 0
    fake_count = 0
    for p in posts:
        if p['is_fake']:
            fake_count += 1
        else:
            sentiment_counts[p['sentiment_label']] += 1
            total_sentiment += p['sentiment_score']
            real_count += 1

    avg_sentiment = round(total_sentiment / real_count, 3) if real_count else 0

    return {
        "query": query,
        "total_comments": len(posts),
        "sentiment_summary": sentiment_counts,
        "avg_sentiment": avg_sentiment,
        "fake_comments_detected": fake_count,
        "ai_insight": ai_insight,
        "comments": posts
    }

# ---------- Serve Frontend ----------

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(static_dir, "index.html"))