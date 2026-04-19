# Stock Sentiment Engine

> Real-time financial sentiment analysis using FinBERT — confidence-weighted market signals with plain-English explainability.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square)
![FinBERT](https://img.shields.io/badge/Model-FinBERT-orange?style=flat-square)
![SQLite](https://img.shields.io/badge/DB-SQLite-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## What it does

Type a stock ticker → get a **Bullish / Bearish / Neutral** signal backed by real news.

The app fetches live headlines from NewsAPI, runs each one through **FinBERT** (a BERT model fine-tuned on financial text), and aggregates the results using confidence-weighted scoring. High-certainty headlines count more than ambiguous ones. Every result explains *why* the signal is what it is.

![Demo](https://via.placeholder.com/900x500/050505/00ff9c?text=Add+your+demo+GIF+here)

---

## Architecture

```
User types "TSLA"
       │
       ▼
 FastAPI Backend
       │
       ├──► NewsAPI → 10 live headlines
       │
       ├──► Yahoo Finance → current price + % change
       │
       ├──► FinBERT (HuggingFace) → sentiment per headline
       │         positive | negative | neutral
       │         + confidence score (0.0 – 1.0)
       │
       ├──► Confidence-weighted aggregation
       │         score = Σ(confidence × vote) per label
       │         winner = label with highest weighted score
       │
       ├──► Explainability engine
       │         top 3 driving headlines + certainty note
       │
       ├──► SQLite → save result to history
       │
       └──► JSON response → frontend dashboard
```

---

## Key Engineering Decisions

### Why FinBERT instead of a generic sentiment model?

Generic models (VADER, TextBlob) are trained on social media and reviews. They misread financial language. "Tesla beats earnings" might score neutral because "beats" is informal. FinBERT is trained on financial news, earnings reports, and analyst notes — it understands the domain.

### Why confidence-weighted scoring instead of majority vote?

Majority vote treats a 51% confident headline the same as a 96% confident one. If 4 headlines are neutral at 55% confidence and 3 are negative at 92% confidence, majority vote says "neutral" but the weighted score says "bearish" — which is the more reliable signal.

```python
# Simple majority vote (old approach — wrong)
winner = max(counts, key=counts.get)

# Confidence-weighted scoring (current approach)
for sentiment, confidence in results:
    weighted_scores[sentiment] += confidence
winner = max(weighted_scores, key=weighted_scores.get)
```

### Why serve the frontend through FastAPI?

Serving `index.html` as a FastAPI static file means frontend and backend share the same origin (`localhost:8000`). This eliminates CORS issues entirely — no proxy config, no extra server, one command to run everything.

---

## Features

- **FinBERT inference** — domain-specific financial NLP model (ProsusAI/finbert)
- **Confidence-weighted signals** — Bullish / Bearish / Neutral with weighted aggregation
- **Plain-English explainability** — top 3 headlines driving the signal + confidence note
- **Live price context** — current price + % change today via Yahoo Finance
- **Comparison mode** — analyze two tickers in parallel, side-by-side chart
- **Search history** — every analysis saved to SQLite, filterable by ticker
- **Trend chart** — sentiment trend across your last 10 searches
- **Skeleton loaders** — professional loading states, no blank screens
- **70+ supported tickers** — US tech, Indian IT, Indian banks, crypto, and more

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | FinBERT (ProsusAI/finbert via HuggingFace) |
| Backend | FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy |
| News Data | NewsAPI (free tier) |
| Price Data | yfinance (Yahoo Finance) |
| Frontend | Vanilla HTML/CSS/JavaScript + Chart.js |
| Charts | Chart.js (donut + bar + line) |

---

## Project Structure

```
stock-sentiment/
├── backend/
│   ├── main.py          ← FastAPI app + all routes
│   ├── model.py         ← FinBERT loading + inference + batch processing
│   ├── news.py          ← NewsAPI integration + ticker→company mapping
│   ├── database.py      ← SQLAlchemy models + save/read history
│   ├── .env.example     ← environment variable template
│   └── requirements.txt
├── frontend/
│   └── index.html       ← single-page dashboard (no build step)
└── README.md
```

---

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/bhanuchukka2005-spec/stock-sentiment-engine
cd stock-sentiment-engine/backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get a free NewsAPI key

Sign up at [newsapi.org](https://newsapi.org) — free tier gives 100 requests/day.

```bash
cp .env.example .env
# Edit .env and add your key:
# NEWSAPI_KEY=your_key_here
```

### 3. Run

```bash
uvicorn main:app --reload
```

Open **http://localhost:8000** in your browser.

> First run downloads FinBERT (~500MB). Cached after that — subsequent starts are instant.

---

## API Reference

All endpoints are documented interactively at `http://localhost:8000/docs`

### `GET /analyze/{ticker}`

Full analysis pipeline for a stock ticker.

**Parameters:**
| Name | Type | Default | Description |
|---|---|---|---|
| `ticker` | path | required | Stock symbol (TSLA, AAPL, TCS, etc.) |
| `max_headlines` | query | 10 | Number of headlines to analyze (1–20) |

**Response:**
```json
{
  "ticker": "TSLA",
  "company": "Tesla",
  "overall_signal": "bearish",
  "avg_confidence": 0.7812,
  "headline_count": 10,
  "breakdown": { "positive": 2, "negative": 6, "neutral": 2 },
  "weighted_scores": { "positive": 18.4, "negative": 58.2, "neutral": 23.4 },
  "price": {
    "price": 248.50,
    "change_pct": -2.14,
    "currency": "USD"
  },
  "explanation": {
    "summary": "Signal is BEARISH — 6 of 10 headlines are negative (60%), carrying 58.2% of weighted confidence.",
    "driver": "Negative headlines carry 58.2% of the confidence-weighted score, vs 18.4% for the opposing signal.",
    "top_headlines": [...],
    "confidence_note": "Moderate confidence — some headlines are ambiguous. Treat signal with caution.",
    "signal_word": "BEARISH"
  },
  "headlines": [
    {
      "title": "Tesla misses delivery estimates for Q3",
      "source": "Reuters",
      "sentiment": "negative",
      "confidence": 0.9341,
      "scores": { "negative": 0.9341, "neutral": 0.0482, "positive": 0.0177 }
    }
  ]
}
```

### `GET /history`

Fetch past searches.

```bash
GET /history              # last 20 searches
GET /history?ticker=TSLA  # last 20 TSLA searches
GET /history?limit=5      # last 5 searches
```

### `GET /stats/{ticker}`

Aggregated signal stats for a ticker across all searches.

### `GET /analyze/headline`

Analyze a single piece of text.

```bash
GET /analyze/headline?text=Apple+reports+record+quarterly+revenue
```

---

## Supported Tickers

The app works with any ticker NewsAPI can find articles for. These have optimized company-name search:

**US Tech:** AAPL, GOOGL, MSFT, AMZN, META, NVDA, TSLA, NFLX, UBER, AMD, INTC, PYPL, SHOP, COIN, PLTR

**Indian IT:** TCS, INFY, WIPRO, HCL, TECHM, LTIM, MPHASIS, COFORGE, PERSISTENT

**Indian Finance:** RELIANCE, HDFC, ICICI, SBI, AXIS, KOTAK, BAJAJ, ADANI

**Indian Consumer:** ZOMATO, PAYTM, NYKAA, MARUTI, TATAMOTORS, ITC

**Global:** SAMSUNG, SONY, TOYOTA, HSBC, BITCOIN, ETHEREUM

> Any ticker not in this list still works — the app searches by ticker symbol directly.

---

## Known Limitations

**FinBERT struggles with informal language.** "Tesla crushes earnings" may score negative because "crushes" is not formal financial vocabulary. The model performs best on Reuters/Bloomberg-style headlines.

**NewsAPI free tier = 100 requests/day.** Each `/analyze/{ticker}` call uses 1 request. For development this is sufficient; production would need a paid tier or a different news source.

**No real-time streaming.** Headlines are fetched on-demand, not pushed. For live streaming you'd need a WebSocket-based ingestion layer.

---

## What I Learned Building This

- **Domain matters in NLP.** Swapping a generic sentiment model for FinBERT improved signal accuracy noticeably on financial text. The right pre-trained model beats the best fine-tuning on the wrong base.
- **Explainability is engineering, not research.** Adding the "why" to every prediction (top headlines, confidence note) took 30 lines of Python and made the tool significantly more trustworthy.
- **Serving frontend through the backend eliminates CORS entirely.** FastAPI's `StaticFiles` mount means one origin, one server, zero configuration.

---

## Author

**Ch. Bhanu Prakash**
CS Engineering, Presidency University, Bengaluru

- GitHub: [github.com/bhanuchukka2005-spec](https://github.com/bhanuchukka2005-spec)
- LinkedIn: [linkedin.com/in/chukka-bhanu-prakash](https://www.linkedin.com/in/chukka-bhanu-prakash)
- LeetCode: [leetcode.com/u/Bhanu_heroo7](https://leetcode.com/u/Bhanu_heroo7)