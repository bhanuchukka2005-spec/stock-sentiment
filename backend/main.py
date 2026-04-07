# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from model import analyze_sentiment, analyze_batch
from news import fetch_headlines, get_company_name
from database import save_search, get_search_history, get_ticker_stats

app = FastAPI(title="Stock Sentiment Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "online", "message": "Stock Sentiment Engine running"}


@app.get("/analyze/headline")
def analyze_single_headline(text: str):
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    result = analyze_sentiment(text)
    return {
        "input": text,
        "label": result["label"],
        "confidence": result["confidence"],
        "scores": result["scores"],
    }


@app.get("/analyze/{ticker}")
def analyze_ticker(ticker: str, max_headlines: int = 10):
    ticker = ticker.upper()
    company_name = get_company_name(ticker)

    try:
        headlines = fetch_headlines(ticker, company_name, max_results=max_headlines)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch news: {str(e)}")

    if not headlines:
        raise HTTPException(status_code=404, detail=f"No headlines found for {ticker}.")

    texts = [h["full_text"] for h in headlines]
    sentiments = analyze_batch(texts)

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0
    for s in sentiments:
        counts[s["label"]] += 1
        total_confidence += s["confidence"]

    overall_signal = max(counts, key=counts.get)
    avg_confidence = round(total_confidence / len(sentiments), 4)

    result = {
        "ticker": ticker,
        "company": company_name or ticker,
        "overall_signal": overall_signal,
        "avg_confidence": avg_confidence,
        "headline_count": len(headlines),
        "breakdown": counts,
        "headlines": [
            {
                "title": h["title"],
                "source": h["source"],
                "published_at": h["published_at"],
                "url": h["url"],
                "sentiment": s["label"],
                "confidence": s["confidence"],
                "scores": s["scores"],
            }
            for h, s in zip(headlines, sentiments)
        ],
    }

    try:
        save_search(ticker, company_name or ticker, result)
    except Exception as e:
        print(f"Warning: could not save to database: {e}")

    return result


@app.get("/history")
def get_history(ticker: str = None, limit: int = 20):
    return get_search_history(ticker=ticker, limit=limit)


@app.get("/stats/{ticker}")
def ticker_stats(ticker: str):
    stats = get_ticker_stats(ticker)
    if stats["total_searches"] == 0:
        raise HTTPException(status_code=404, detail=f"No history found for {ticker}")
    return stats


# ── IMPORTANT: this must be LAST — after all routes ──────────────────────────
# Serves frontend/index.html at http://localhost:8000/
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")