"""
Tests for Stock Sentiment Engine API.
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


# ── Single headline analysis ──────────────────────────────────────────────────

@patch("main.analyze_sentiment")
def test_analyze_headline_positive(mock_sentiment):
    mock_sentiment.return_value = {
        "label": "positive",
        "confidence": 0.94,
        "scores": {"positive": 0.94, "negative": 0.03, "neutral": 0.03}
    }
    response = client.get("/analyze/headline?text=Apple reports record quarterly revenue")
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "positive"
    assert data["confidence"] == 0.94
    assert "scores" in data


def test_analyze_headline_empty_text():
    response = client.get("/analyze/headline?text=")
    assert response.status_code == 400


def test_analyze_headline_missing_text():
    response = client.get("/analyze/headline")
    assert response.status_code == 422   # FastAPI validation error


# ── Ticker analysis ───────────────────────────────────────────────────────────

@patch("main.fetch_headlines")
@patch("main.analyze_batch")
@patch("main.get_price_data")
@patch("main.save_search")
def test_analyze_ticker_success(mock_save, mock_price, mock_batch, mock_headlines):
    mock_headlines.return_value = [
        {
            "title": "Tesla earnings beat estimates",
            "description": "Strong Q3 results",
            "full_text": "Tesla earnings beat estimates. Strong Q3 results",
            "url": "https://example.com",
            "published_at": "2025-04-01T10:00:00Z",
            "source": "Reuters",
        },
        {
            "title": "Tesla stock rises after delivery numbers",
            "description": "Deliveries up 20%",
            "full_text": "Tesla stock rises after delivery numbers. Deliveries up 20%",
            "url": "https://example.com/2",
            "published_at": "2025-04-01T09:00:00Z",
            "source": "Bloomberg",
        }
    ]
    mock_batch.return_value = [
        {"label": "positive", "confidence": 0.91, "scores": {"positive": 0.91, "negative": 0.05, "neutral": 0.04}},
        {"label": "positive", "confidence": 0.87, "scores": {"positive": 0.87, "negative": 0.08, "neutral": 0.05}},
    ]
    mock_price.return_value = {"price": 248.50, "change_pct": 2.1, "currency": "USD", "change_abs": 5.1, "prev_close": 243.4}
    mock_save.return_value = None

    response = client.get("/analyze/TSLA")
    assert response.status_code == 200
    data = response.json()

    assert data["ticker"] == "TSLA"
    assert data["overall_signal"] in ["positive", "negative", "neutral"]
    assert "breakdown" in data
    assert "weighted_scores" in data
    assert "explanation" in data
    assert "headlines" in data
    assert len(data["headlines"]) == 2


@patch("main.fetch_headlines")
def test_analyze_ticker_no_headlines(mock_headlines):
    mock_headlines.return_value = []
    response = client.get("/analyze/XYZUNKNOWN999")
    assert response.status_code == 404


@patch("main.fetch_headlines")
def test_analyze_ticker_news_api_error(mock_headlines):
    mock_headlines.side_effect = Exception("NewsAPI unavailable")
    response = client.get("/analyze/AAPL")
    assert response.status_code == 503


# ── Ticker is uppercased ──────────────────────────────────────────────────────

@patch("main.fetch_headlines")
@patch("main.analyze_batch")
@patch("main.get_price_data")
@patch("main.save_search")
def test_ticker_uppercased(mock_save, mock_price, mock_batch, mock_headlines):
    mock_headlines.return_value = [{
        "title": "Test", "description": "", "full_text": "Test",
        "url": "https://x.com", "published_at": "2025-01-01T00:00:00Z", "source": "Test"
    }]
    mock_batch.return_value = [{"label": "neutral", "confidence": 0.7, "scores": {"neutral": 0.7, "positive": 0.2, "negative": 0.1}}]
    mock_price.return_value = None
    mock_save.return_value = None

    response = client.get("/analyze/tsla")   # lowercase
    assert response.status_code == 200
    assert response.json()["ticker"] == "TSLA"   # uppercased in response


# ── History ───────────────────────────────────────────────────────────────────

@patch("main.get_search_history")
def test_get_history(mock_history):
    mock_history.return_value = [
        {"id": 1, "ticker": "TSLA", "company": "Tesla", "signal": "bearish",
         "avg_confidence": 0.78, "headline_count": 10,
         "breakdown": {"positive": 2, "negative": 6, "neutral": 2},
         "created_at": "2025-04-01T10:00:00"}
    ]
    response = client.get("/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ticker"] == "TSLA"


@patch("main.get_search_history")
def test_get_history_filtered_by_ticker(mock_history):
    mock_history.return_value = []
    response = client.get("/history?ticker=AAPL&limit=5")
    assert response.status_code == 200
    mock_history.assert_called_once_with(ticker="AAPL", limit=5)


# ── Stats ─────────────────────────────────────────────────────────────────────

@patch("main.get_ticker_stats")
def test_ticker_stats_found(mock_stats):
    mock_stats.return_value = {
        "ticker": "TSLA",
        "total_searches": 3,
        "signal_history": ["bearish", "neutral", "bearish"],
        "most_common_signal": "bearish"
    }
    response = client.get("/stats/TSLA")
    assert response.status_code == 200
    assert response.json()["most_common_signal"] == "bearish"


@patch("main.get_ticker_stats")
def test_ticker_stats_not_found(mock_stats):
    mock_stats.return_value = {"ticker": "XYZ", "total_searches": 0}
    response = client.get("/stats/XYZ")
    assert response.status_code == 404
