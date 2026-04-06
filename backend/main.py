# main.py

from fastapi import FastAPI, HTTPException
from model import analyze_sentiment, analyze_batch
from news import fetch_headlines, get_company_name

app = FastAPI(title="Stock Sentiment Engine", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "online", "message": "Stock Sentiment Engine running"}


@app.get("/analyze/headline")
def analyze_single_headline(text: str):
    """Analyze sentiment of a single headline."""
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
    """
    Full analysis pipeline for a stock ticker.
    
    1. Fetch real headlines from NewsAPI
    2. Run FinBERT on each headline
    3. Aggregate into overall market signal
    
    max_headlines is a query parameter with a default value of 10.
    User can override: /analyze/TSLA?max_headlines=20
    """
    ticker = ticker.upper()
    
    # Step 1: get company name for better search results
    company_name = get_company_name(ticker)
    
    # Step 2: fetch real headlines
    try:
        headlines = fetch_headlines(ticker, company_name, max_results=max_headlines)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch news: {str(e)}")
    
    if not headlines:
        raise HTTPException(
            status_code=404,
            detail=f"No headlines found for {ticker}. Try a different ticker."
        )
    
    # Step 3: run FinBERT on all headlines at once (batch = faster)
    texts = [h["full_text"] for h in headlines]
    sentiments = analyze_batch(texts)
    
    # Step 4: aggregate results
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0
    
    for s in sentiments:
        counts[s["label"]] += 1
        total_confidence += s["confidence"]
    
    # Overall signal = label with most headlines
    overall_signal = max(counts, key=counts.get)
    avg_confidence = round(total_confidence / len(sentiments), 4)
    
    # Step 5: build the response
    return {
        "ticker": ticker,
        "company": company_name or ticker,
        "overall_signal": overall_signal,
        "avg_confidence": avg_confidence,
        "headline_count": len(headlines),
        "breakdown": counts,
        # Combine headline data with its sentiment result
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