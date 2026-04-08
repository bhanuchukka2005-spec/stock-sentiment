# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from model import analyze_sentiment, analyze_batch
from news import fetch_headlines, get_company_name, get_price_data
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


def generate_explanation(ticker, overall_signal, counts, weighted_scores,
                          headlines_with_sentiment, avg_confidence):
    total = sum(counts.values())
    dominant = overall_signal
    signal_word = {"positive": "BULLISH", "negative": "BEARISH", "neutral": "NEUTRAL"}[dominant]
    dominant_count  = counts[dominant]
    dominant_pct    = round(dominant_count / total * 100)
    dominant_weight = weighted_scores[dominant]

    summary = (
        f"Signal is {signal_word} — "
        f"{dominant_count} of {total} headlines are {dominant} "
        f"({dominant_pct}%), carrying {dominant_weight:.1f}% of weighted confidence."
    )
    opposing = "positive" if dominant != "positive" else "negative"
    driver = (
        f"{dominant.capitalize()} headlines carry {dominant_weight:.1f}% "
        f"of the confidence-weighted score, vs "
        f"{weighted_scores.get(opposing, 0):.1f}% for the opposing signal."
    )
    supporting = sorted(
        [h for h in headlines_with_sentiment if h["sentiment"] == dominant],
        key=lambda x: x["confidence"], reverse=True
    )
    top_headlines = [
        {"title": h["title"], "source": h["source"],
         "sentiment": h["sentiment"], "confidence": h["confidence"]}
        for h in supporting[:3]
    ]
    high_conf = sum(1 for h in headlines_with_sentiment if h["confidence"] >= 0.80)
    if avg_confidence >= 0.80:
        conf_note = f"High confidence — model is certain on {high_conf} of {total} headlines."
    elif avg_confidence >= 0.65:
        conf_note = "Moderate confidence — some headlines are ambiguous. Treat signal with caution."
    else:
        conf_note = "Low confidence — headlines are mixed or ambiguous. Signal may not be reliable."

    return {
        "summary": summary, "driver": driver,
        "top_headlines": top_headlines,
        "confidence_note": conf_note, "signal_word": signal_word,
    }


@app.get("/analyze/{ticker}")
def analyze_ticker(ticker: str, max_headlines: int = 10):
    ticker = ticker.upper()
    company_name = get_company_name(ticker)

    # Fetch price — non-blocking, None if unavailable
    price_data = get_price_data(ticker)

    try:
        headlines = fetch_headlines(ticker, company_name, max_results=max_headlines)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch news: {str(e)}")

    if not headlines:
        raise HTTPException(status_code=404, detail=f"No headlines found for {ticker}.")

    texts     = [h["full_text"] for h in headlines]
    sentiments = analyze_batch(texts)

    counts          = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    weighted_scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    total_confidence = 0.0

    for s in sentiments:
        counts[s["label"]]          += 1
        weighted_scores[s["label"]] += s["confidence"]
        total_confidence            += s["confidence"]

    # Convert counts back to int for display
    counts = {k: int(v) for k, v in counts.items()}

    overall_signal = max(weighted_scores, key=weighted_scores.get)
    avg_confidence = round(total_confidence / len(sentiments), 4)

    total_weight = sum(weighted_scores.values())
    weighted_pct = {k: round(v / total_weight * 100, 1) for k, v in weighted_scores.items()}

    headlines_with_sentiment = [
        {
            "title":        h["title"],
            "source":       h["source"],
            "published_at": h["published_at"],
            "url":          h["url"],
            "sentiment":    s["label"],
            "confidence":   s["confidence"],
            "scores":       s["scores"],
        }
        for h, s in zip(headlines, sentiments)
    ]

    explanation = generate_explanation(
        ticker=ticker,
        overall_signal=overall_signal,
        counts=counts,
        weighted_scores=weighted_pct,
        headlines_with_sentiment=headlines_with_sentiment,
        avg_confidence=avg_confidence,
    )

    result = {
        "ticker":          ticker,
        "company":         company_name or ticker,
        "overall_signal":  overall_signal,
        "avg_confidence":  avg_confidence,
        "headline_count":  len(headlines),
        "breakdown":       counts,
        "weighted_scores": weighted_pct,
        "price":           price_data,
        "explanation":     explanation,
        "headlines":       headlines_with_sentiment,
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


# MUST be last — after all routes
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")