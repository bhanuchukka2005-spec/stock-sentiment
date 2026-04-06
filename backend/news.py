# news.py

import requests
import os
from dotenv import load_dotenv

# load_dotenv() reads your .env file and makes the values
# available via os.getenv(). This is how we keep keys out of code.
load_dotenv()


def fetch_headlines(ticker: str, company_name: str = None, max_results: int = 10) -> list[dict]:
    """
    Fetch real news headlines for a stock ticker.
    
    Why do we also accept company_name?
    Searching "AAPL" might miss articles that say "Apple" not "AAPL".
    So we search both and combine results.
    
    Returns a list of dicts:
    [
        {
            "title": "Apple reports record revenue...",
            "description": "Apple Inc. reported...",
            "url": "https://...",
            "published_at": "2024-01-15T10:30:00Z",
            "source": "Reuters"
        },
        ...
    ]
    """
    api_key = os.getenv("NEWSAPI_KEY")
    
    if not api_key:
        raise ValueError("NEWSAPI_KEY not found in .env file")
    
    # Build the search query
    # If we have a company name, search for both ticker AND company name
    # "OR" means: give me articles mentioning either one
    if company_name:
        query = f"{ticker} OR {company_name}"
    else:
        query = ticker
    
    # This is the NewsAPI endpoint
    # "everything" endpoint gives us all articles (not just top headlines)
    url = "https://newsapi.org/v2/everything"
    
    # These are the parameters we're sending with our request
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",     # most recent first
        "pageSize": max_results,      # how many articles to return
        "apiKey": api_key,
    }
    
    # requests.get() sends an HTTP GET request to the URL
    # It's the same as typing a URL in your browser, but from code
    response = requests.get(url, params=params)
    
    # HTTP status 200 means success
    # If something went wrong (401 = bad key, 429 = rate limited, etc.)
    # raise_for_status() throws an error automatically
    response.raise_for_status()
    
    # .json() converts the response body from a JSON string into a Python dict
    data = response.json()
    
    # data looks like:
    # {
    #   "status": "ok",
    #   "totalResults": 38,
    #   "articles": [
    #     {"title": "...", "description": "...", "url": "...", ...},
    #     ...
    #   ]
    # }
    
    articles = data.get("articles", [])
    
    # Clean and return only what we need
    headlines = []
    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")
        
        # Skip articles with no useful content
        # "[Removed]" is what NewsAPI returns for deleted articles
        if not title or title == "[Removed]":
            continue
        
        headlines.append({
            "title": title,
            "description": description or "",
            # Combine title + description for richer sentiment analysis
            # More context = better model accuracy
            "full_text": f"{title}. {description}" if description else title,
            "url": article.get("url", ""),
            "published_at": article.get("publishedAt", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
        })
    
    return headlines


# A hardcoded mapping of common tickers to company names
# We'll use this so our searches are more accurate
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "GOOGL": "Google",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "META": "Meta Facebook",
    "NVDA": "Nvidia",
    "NFLX": "Netflix",
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "INFY": "Infosys",
    "WIPRO": "Wipro",
    "HDFC": "HDFC Bank",
}


def get_company_name(ticker: str) -> str | None:
    """Look up company name for a ticker. Returns None if not found."""
    return TICKER_TO_COMPANY.get(ticker.upper())