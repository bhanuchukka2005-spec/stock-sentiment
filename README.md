# 📈 Stock Sentiment Engine

> Real-time financial sentiment analysis using FinBERT — confidence-weighted Bullish / Bearish / Neutral signals with plain-English explainability.

[![CI](https://github.com/bhanuchukka2005-spec/stock-sentiment-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/bhanuchukka2005-spec/stock-sentiment-engine/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)
![FinBERT](https://img.shields.io/badge/Model-FinBERT-orange?style=flat-square)
![SQLite](https://img.shields.io/badge/DB-SQLite-003B57?style=flat-square&logo=sqlite)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## What it does

Type any stock ticker → get a **Bullish / Bearish / Neutral** signal backed by live news.

Fetches real headlines from NewsAPI, runs each through **FinBERT** (a BERT model fine-tuned specifically on financial text), and aggregates results using **confidence-weighted scoring** — high-certainty headlines count more than ambiguous ones. Every result explains *why* the signal is what it is.

---

## Architecture

```
User types "TSLA"
       │
       ▼
 FastAPI Backend
       │
       ├──► NewsAPI          → 10 live headlines
       ├──► Yahoo Finance    → current price + % change today
       ├──► FinBERT          → sentiment + confidence per headline
       ├──► Weighted aggregation → overall signal
       ├──► Explainability   → top 3 driving headlines + certainty note
       ├──► SQLite           → save to history
       └──► JSON response    → frontend dashboard
```

---

## Key Engineering Decisions

**Why FinBERT over VADER or TextBlob?**
Generic models are trained on social media and reviews. They misread financial language — "Tesla crushes earnings" can score neutral because "crushes" is informal. FinBERT is trained on earnings reports, analyst notes, and financial news. It understands the domain.

**Why confidence-weighted scoring over majority vote?**
Majority vote treats a 51% confident headline the same as a 96% confident one. Weighted scoring means a strongly negative headline at 94% confidence outweighs three weakly neutral ones at 52%.

```python
# Majority vote — wrong
winner = max(counts, key=counts.get)

# Confidence-weighted — correct
for sentiment, confidence in results:
    weighted_scores[sentiment] += confidence
winner = max(weighted_scores, key=weighted_scores.get)
```

**Why serve frontend through FastAPI?**
Mounting `frontend/` as FastAPI static files means one origin, one server, zero CORS configuration.

---

## Features

- FinBERT inference — financial domain NLP (ProsusAI/finbert)
- Confidence-weighted Bullish / Bearish / Neutral signals
- Plain-English explainability per result
- Live price + % change via Yahoo Finance
- Compare mode — two tickers analysed in parallel
- Search history with trend chart — SQLite persistence
- Skeleton loaders, donut chart, confidence bar chart
- 70+ supported tickers — US, Indian IT, Indian banks, crypto

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | FinBERT (ProsusAI/finbert) via HuggingFace |
| Backend | FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy |
| News | NewsAPI (free tier) |
| Price | yfinance (Yahoo Finance) |
| Frontend | Vanilla HTML/CSS/JS + Chart.js |
| CI/CD | GitHub Actions |
| Container | Docker |

---

## Project Structure

```
stock-sentiment-engine/
├── backend/
│   ├── main.py            ← FastAPI app + all routes
│   ├── model.py           ← FinBERT loading + batch inference
│   ├── news.py            ← NewsAPI + ticker→company mapping
│   ├── database.py        ← SQLAlchemy models + history
│   ├── tests/
│   │   └── test_api.py    ← pytest test suite
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── index.html         ← single-page dashboard
├── .github/
│   └── workflows/
│       ├── ci.yml         ← lint + security + tests
│       └── deploy.yml     ← auto-deploy to Railway
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### Local (without Docker)

```bash
git clone https://github.com/bhanuchukka2005-spec/stock-sentiment-engine
cd stock-sentiment-engine/backend

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Add your NEWSAPI_KEY to .env

uvicorn main:app --reload
```

Open **http://localhost:8000**

> First run downloads FinBERT (~500MB). Cached after that.

### With Docker

```bash
cp backend/.env.example backend/.env
# Add your NEWSAPI_KEY

docker-compose up --build
```

---

## API Reference

Interactive docs at `http://localhost:8000/docs`

### `GET /analyze/{ticker}`

```bash
GET /analyze/TSLA
GET /analyze/TSLA?max_headlines=15
```

**Response:**
```json
{
  "ticker": "TSLA",
  "company": "Tesla",
  "overall_signal": "bearish",
  "avg_confidence": 0.7812,
  "breakdown": { "positive": 2, "negative": 6, "neutral": 2 },
  "weighted_scores": { "positive": 18.4, "negative": 58.2, "neutral": 23.4 },
  "price": { "price": 248.50, "change_pct": -2.14, "currency": "USD" },
  "explanation": {
    "summary": "Signal is BEARISH — 6 of 10 headlines are negative (60%)",
    "top_headlines": [...],
    "confidence_note": "High confidence — model is certain on 7 of 10 headlines."
  }
}
```

### `GET /history`
```bash
GET /history
GET /history?ticker=TSLA
GET /history?limit=5
```

### `GET /stats/{ticker}`
### `GET /analyze/headline?text=...`

---

## Environment Variables

```bash
NEWSAPI_KEY=your_newsapi_key_here   # required — get free at newsapi.org
```

---

## Known Limitations

- FinBERT struggles with informal financial language ("crushes", "smashes")
- NewsAPI free tier = 100 requests/day
- No real-time streaming — headlines fetched on-demand

---

## Interview Q&A

**Q: Why FinBERT specifically?**
FinBERT is BERT fine-tuned on financial corpora. Generic sentiment models misclassify financial language because the training domain is wrong.

**Q: What's the difference between training and inference here?**
We don't train anything — we load a pre-trained model and run inference only. Training happened on HuggingFace's infrastructure using financial datasets.

**Q: How does the explainability work?**
After inference, we sort headlines by confidence score, filter to the dominant sentiment label, and return the top 3 as "driving headlines." It's logic, not a separate ML model.

**Q: What would you add in production?**
Rate limiting, user authentication, a proper vector database for semantic search over history, and a WebSocket layer for real-time streaming instead of on-demand fetch.

---

## Author

**Ch. Bhanu Prakash** — CS Engineering, Presidency University, Bengaluru

[GitHub](https://github.com/bhanuchukka2005-spec) · [LinkedIn](https://linkedin.com/in/chukka-bhanu-prakash) · [LeetCode](https://leetcode.com/u/Bhanu_heroo7)
