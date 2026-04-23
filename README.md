# Stock Sentiment Engine

> Real-time financial sentiment analysis using FinBERT — confidence-weighted market signals with plain-English explainability.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green?style=flat-square)
![FinBERT](https://img.shields.io/badge/Model-FinBERT-orange?style=flat-square)
![SQLite](https://img.shields.io/badge/DB-SQLite-lightgrey?style=flat-square)
![CI](https://img.shields.io/github/actions/workflow/status/bhanuchukka2005-spec/stock-sentiment-engine/ci.yml?label=CI&style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## What it does

Type a stock ticker → get a **Bullish / Bearish / Neutral** signal backed by real news.

The app fetches live headlines from NewsAPI, runs each one through **FinBERT** (a BERT model fine-tuned on financial text), and aggregates the results using confidence-weighted scoring. High-certainty headlines count more than ambiguous ones. Every result explains *why* the signal is what it is.

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
| CI/CD | GitHub Actions |

---

## Project Structure

```
stock-sentiment/
├── .github/
│   └── workflows/
│       ├── ci.yml           ← lint, test, model smoke-test on every push/PR
│       └── deploy.yml       ← deploy to server on push to main
├── backend/
│   ├── main.py              ← FastAPI app + all routes
│   ├── model.py             ← FinBERT loading + inference + batch processing
│   ├── news.py              ← NewsAPI integration + ticker→company mapping
│   ├── database.py          ← SQLAlchemy models + save/read history
│   ├── test_model.py        ← unit tests for sentiment model
│   ├── test_news.py         ← unit tests for news fetching
│   ├── .env.example         ← environment variable template
│   └── requirements.txt
├── frontend/
│   └── index.html           ← single-page dashboard (no build step)
├── LICENSE
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
# Edit .env and paste your key as: NEWSAPI_KEY=your_key_here
```

### 3. Run

```bash
uvicorn main:app --reload
```

Open **http://localhost:8000** in your browser.

> First run downloads FinBERT (~500MB). Cached after that — subsequent starts are instant.

---

## CI/CD — GitHub Actions

This project uses two GitHub Actions workflows.

**`ci.yml`** runs on every push and pull request. It installs dependencies, runs flake8 linting, and executes the full pytest suite. The HuggingFace model and pip packages are both cached so runs after the first are fast. PRs cannot be merged if this workflow fails.

**`deploy.yml`** runs only when code lands on `main`. It SSHs into the production server, pulls the latest code, reinstalls any changed dependencies, and restarts the app via systemctl.

### CI/CD Flow

```
Developer pushes code
        │
        ▼
  CI workflow runs
        │
        ├── flake8 lint
        ├── pytest (model + news tests)
        └── pass / fail ← PR is blocked if this fails

Merge PR into main
        │
        ▼
  Deploy workflow runs
        │
        ├── SSH into server
        ├── git pull
        ├── pip install
        └── systemctl restart ← app is live with new code
```

### GitHub Secrets required

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Description |
|---|---|
| `NEWSAPI_KEY` | Your NewsAPI key — used in CI tests |
| `DEPLOY_HOST` | IP address or domain of your server |
| `DEPLOY_USER` | SSH username on your server (e.g. `ubuntu`) |
| `DEPLOY_SSH_KEY` | Your private SSH key (contents of `~/.ssh/id_rsa`) |

The workflow YAML files live in `.github/workflows/` in the repo.

---

## API Reference

All endpoints are documented interactively at `http://localhost:8000/docs`.

### `GET /analyze/{ticker}`

Full analysis pipeline for a stock ticker. Returns the overall signal, confidence breakdown, weighted scores, current price, plain-English explanation, and all headlines with their individual sentiments.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticker` | path | required | Stock symbol (TSLA, AAPL, TCS, etc.) |
| `max_headlines` | query | 10 | Number of headlines to analyze (1–20) |

### `GET /history`

Returns past searches. Pass `?ticker=TSLA` to filter by symbol, `?limit=5` to cap results. Defaults to the last 20 searches across all tickers.

### `GET /stats/{ticker}`

Returns aggregated signal stats for a ticker — total searches, signal history, signal counts, and the most common signal over time.

### `GET /analyze/headline`

Analyze a single piece of text directly. Pass the text as a `?text=` query parameter. Useful for testing the model on arbitrary headlines without fetching news.

---

## Supported Tickers

The app works with any ticker NewsAPI can find articles for. These have optimized company-name queries built in:

**US Tech:** AAPL, GOOGL, MSFT, AMZN, META, NVDA, TSLA, NFLX, UBER, AMD, INTC, PYPL, SHOP, COIN, PLTR

**Indian IT:** TCS, INFY, WIPRO, HCL, TECHM, LTIM, MPHASIS, COFORGE, PERSISTENT

**Indian Finance:** RELIANCE, HDFC, ICICI, SBI, AXIS, KOTAK, BAJAJ, ADANI

**Indian Consumer:** ZOMATO, PAYTM, NYKAA, MARUTI, TATAMOTORS, ITC

**Global:** SAMSUNG, SONY, TOYOTA, HSBC, BITCOIN, ETHEREUM

Any ticker not in this list still works — the app searches by ticker symbol directly.

---

## Known Limitations

**FinBERT struggles with informal language.** Phrases like "Tesla crushes earnings" may score incorrectly because the model is trained on formal financial text. It performs best on Reuters/Bloomberg-style headlines.

**NewsAPI free tier = 100 requests/day.** Each `/analyze/{ticker}` call uses one request. Sufficient for development; production would need a paid plan or a different news source.

**No real-time streaming.** Headlines are fetched on-demand, not pushed. Live streaming would require a WebSocket-based ingestion layer.

---

## What I Learned Building This

- **Domain matters in NLP.** Swapping a generic sentiment model for FinBERT improved signal accuracy noticeably on financial text. The right pre-trained model beats the best fine-tuning on the wrong base.
- **Explainability is engineering, not research.** Adding the "why" to every prediction took 30 lines of Python and made the tool significantly more trustworthy.
- **Serving frontend through the backend eliminates CORS entirely.** FastAPI's `StaticFiles` mount means one origin, one server, zero configuration.
- **CI gates quality.** Having GitHub Actions block merges on failing tests forces cleaner code discipline across the project.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Author

**Ch. Bhanu Prakash**  
CS Engineering, Presidency University, Bengaluru

- GitHub: [github.com/bhanuchukka2005-spec](https://github.com/bhanuchukka2005-spec)
- LinkedIn: [linkedin.com/in/chukka-bhanu-prakash](https://www.linkedin.com/in/chukka-bhanu-prakash)
- LeetCode: [leetcode.com/u/Bhanu_heroo7](https://leetcode.com/u/Bhanu_heroo7)