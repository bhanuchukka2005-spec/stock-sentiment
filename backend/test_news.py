# test_news.py
import os
import pytest
from unittest.mock import patch, MagicMock
from news import fetch_headlines, get_company_name, get_search_query


# ── Unit tests (no API key needed) ───────────────────────────────────────────

def test_get_company_name_known_ticker():
    assert get_company_name("TSLA") == "Tesla"
    assert get_company_name("AAPL") == "Apple"
    assert get_company_name("TCS") == "Tata Consultancy Services TCS"


def test_get_company_name_unknown_ticker():
    # Unknown tickers return None — that's expected behaviour
    result = get_company_name("XYZ_UNKNOWN")
    assert result is None


def test_get_company_name_case_insensitive():
    assert get_company_name("tsla") == get_company_name("TSLA")
    assert get_company_name("aapl") == get_company_name("AAPL")


def test_get_search_query_known_ticker():
    query = get_search_query("TSLA")
    assert "TSLA" in query
    assert "Tesla" in query


def test_get_search_query_unknown_ticker():
    query = get_search_query("XYZ_UNKNOWN")
    assert "XYZ_UNKNOWN" in query


# ── Integration test (requires NEWSAPI_KEY) ───────────────────────────────────
# Skipped automatically in CI if the secret is not set.

@pytest.mark.skipif(
    not os.getenv("NEWSAPI_KEY"),
    reason="NEWSAPI_KEY not set — skipping live API test"
)
def test_fetch_headlines_live():
    ticker = "TSLA"
    company = get_company_name(ticker)
    headlines = fetch_headlines(ticker, company, max_results=3)

    assert isinstance(headlines, list)
    assert len(headlines) > 0

    first = headlines[0]
    assert "title" in first
    assert "source" in first
    assert "published_at" in first
    assert "url" in first
    assert "full_text" in first


# ── Mocked test (always runs, no API key needed) ──────────────────────────────

def test_fetch_headlines_mocked():
    """
    Test fetch_headlines with a mocked HTTP response.
    Validates that the function correctly parses the NewsAPI response format.
    """
    mock_response = {
        "articles": [
            {
                "title": "Tesla reports record deliveries",
                "description": "Tesla beat analyst expectations.",
                "url": "https://example.com/article1",
                "publishedAt": "2025-04-20T10:00:00Z",
                "source": {"name": "Reuters"},
            },
            {
                "title": "[Removed]",   # should be filtered out
                "description": "",
                "url": "",
                "publishedAt": "",
                "source": {"name": "Unknown"},
            },
        ]
    }

    with patch("news.requests.get") as mock_get, \
         patch("news.os.getenv", return_value="fake-key"):

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        headlines = fetch_headlines("TSLA", "Tesla", max_results=5)

    # [Removed] article should be filtered out
    assert len(headlines) == 1
    assert headlines[0]["title"] == "Tesla reports record deliveries"
    assert headlines[0]["source"] == "Reuters"
    assert "Tesla beat analyst expectations." in headlines[0]["full_text"]