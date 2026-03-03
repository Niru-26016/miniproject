import os, uuid, chromadb
from fastapi import FastAPI, BackgroundTasks
from core.scraper import RedditScraper
from core.bot_shield import BotShield
from core.nlp_engine import NLPEngine
from dotenv import load_dotenv
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Brand Insight Engine")
reddit = RedditScraper()
shield = BotShield()
brain = NLPEngine(api_key=OPENAI_KEY)

# Vector DB initialization
chroma_client = chromadb.PersistentClient(path="./brand_db")
collection = chroma_client.get_or_create_collection(name="human_feedback")

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