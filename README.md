# 🔍 Brand Insight Engine — Sentiment Analysis Dashboard

An advanced, AI-powered product sentiment analysis dashboard that scrapes Reddit, runs extensive heuristic and AI-based evaluations (VADER sentiment, OpenAI emotion detection, trust scoring, and fake post detection) — all displayed in a premium, real-time dark-mode UI.

![Dashboard Preview](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688)

## ✨ Features

- **🔎 Natural Language Search** — Enter any product or brand name (e.g. "iPhone 17", "Samsung S26", "PS5").
- **📡 Rich Reddit Scraping** — Fetches top posts + comments from Reddit (past week, sorted by relevance) pulling over 20+ metadata fields (engagement, author info, timing, etc.).
- **📊 VADER Sentiment Analysis** — Classifies each post as positive, negative, or neutral with a compound polarity score.
- **🤖 AI Fake Post Detection** — Uses OpenAI GPT-4o-mini to identify spam, bot-generated, and promotional content.
- **🎭 Emotion Detection** — Classifies dominant emotions alongside sentiment (Joy, Anger, Fear, Surprise, Sadness, Disgust).
- **🛡️ BotShield** — Comprehensive 17-signal heuristic engine evaluating spam phrases, link density, account age, upvote ratios, text patterns, and more to calculate a Bot Probability Score.
- **✅ Trust & Credibility Scoring** — Evaluates author reputation, engagement, and bot signals to provide a 0-100 Trust Score and High/Medium/Low Credibility ratings per post.
- **🏷️ Aspect-Based Sentiment** — Breaks down sentiment by specific product features (e.g., "camera: positive", "battery: negative").
- **🔑 Keyword Extraction** — Identifies and ranks the top discussed topics or features.
- **💡 Actionable Recommendations** — AI generates prioritized, actionable insights for the brand based on current sentiment patterns.
- **📈 Comprehensive Interactive Charts** — Radar charts, donut charts, and bar charts using Chart.js.
- **⚡ Live Dashboard** — Auto-refreshing UI with countdown timers.
- **💾 ChromaDB Vector Storage** — Background sync to store genuine human feedback for historical tracking.

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Python |
| **NLP & AI** | VADER Sentiment, OpenAI GPT-4o-mini |
| **Scraping** | Reddit JSON API |
| **Vector DB** | ChromaDB |
| **Frontend** | HTML, CSS, JavaScript (Vanilla), Chart.js |
| **Server** | Uvicorn |

## 🚀 Setup & Run

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd miniproject
```

### 2. Create virtual environment
```bash
python -m venv .venv
# Windows CMD:
.venv\Scripts\activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your OpenAI API key
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=sk-your-key-here
REDDIT_POST_LIMIT=15
```

### 5. Run the server
```bash
uvicorn main:app --reload
```

### 6. Open the dashboard
Visit **http://127.0.0.1:8000** in your browser

## 📁 Project Structure

```
miniproject/
├── main.py                  # FastAPI app with API endpoints and scoring logic
├── core/
│   ├── scraper.py           # Advanced Reddit scraper (extracts 20+ metadata fields)
│   ├── bot_shield.py        # 17-signal heuristic bot detection engine
│   └── nlp_engine.py        # OpenAI integration (emotions, aspects, keywords, recommendations)
├── static/
│   ├── index.html           # Full dashboard frontend
│   ├── style.css            # Premium dark-mode styling and animations
│   └── app.js               # Event handling, live updates, and Chart.js rendering
├── requirements.txt
├── .env                     # API keys and limits (git-ignored)
└── .gitignore
```

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the dashboard UI |
| `GET` | `/api/analyze/{query}` | Full pipeline: scrape, VADER, BotShield, OpenAI analysis, Trust & Credibility |
| `POST` | `/api/sync/{brand}` | Background sync: scrape, filter bots, & store in ChromaDB |
| `GET` | `/api/report/{brand}` | Generate high-level AI report from stored (human) data |

## ⚠️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key for advanced analysis |
| `REDDIT_POST_LIMIT`| ❌ | Number of reddit posts to scrape (defaults to 15) |

## 📝 License

This project is for educational purposes.
