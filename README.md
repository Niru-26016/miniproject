# 🔍 Brand Insight Engine — Sentiment Analysis Dashboard

An AI-powered product sentiment analysis dashboard that scrapes Reddit, runs VADER sentiment analysis, and uses OpenAI GPT-4o-mini to detect fake/bot comments — all displayed in a premium dark-mode UI.

![Dashboard Preview](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688)

## ✨ Features

- **🔎 Natural Language Search** — Enter any product or brand name (e.g. "iPhone 17", "Samsung S26", "PS5")
- **📡 Reddit Scraping** — Fetches top posts + comments from Reddit (past week, sorted by relevance)
- **📊 VADER Sentiment Analysis** — Classifies each comment as positive, negative, or neutral with a polarity score
- **🤖 AI Fake Comment Detection** — Uses OpenAI GPT-4o-mini to identify spam, bot-generated, and promotional comments
- **💡 AI-Generated Insights** — Generates a conversational summary identifying top issues and improvement suggestions
- **📈 Interactive Charts** — Sentiment distribution pie chart, per-comment bar chart, and authenticity donut chart
- **🛡️ Bot Shield** — Rule-based pre-filter for obvious spam/bot content
- **💾 ChromaDB Vector Storage** — Stores genuine human feedback for persistent analysis

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python |
| NLP | VADER Sentiment, OpenAI GPT-4o-mini |
| Scraping | Reddit JSON API |
| Vector DB | ChromaDB |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Server | Uvicorn |

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
├── main.py                  # FastAPI app with API endpoints
├── core/
│   ├── scraper.py           # Reddit scraper (posts + comments)
│   ├── bot_shield.py        # Rule-based bot detection
│   └── nlp_engine.py        # OpenAI integration (insights + fake detection)
├── static/
│   ├── index.html           # Dashboard frontend
│   ├── style.css            # Dark-mode styling
│   └── app.js               # Charts, search, table rendering
├── requirements.txt
├── .env                     # API keys (git-ignored)
└── .gitignore
```

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the dashboard UI |
| `GET` | `/api/analyze/{query}` | Full analysis: scrape + sentiment + fake detection + AI insight |
| `POST` | `/api/sync/{brand}` | Background sync: scrape & store in ChromaDB |
| `GET` | `/api/report/{brand}` | Generate AI report from stored data |

## ⚠️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key for fake detection & insights |

## 📝 License

This project is for educational purposes.
