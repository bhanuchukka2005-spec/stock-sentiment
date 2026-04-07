# news.py

import requests
import os
from dotenv import load_dotenv

# load_dotenv() reads your .env file and makes the values
# available via os.getenv(). This is how we keep keys out of code.
load_dotenv()


def fetch_headlines(ticker: str, company_name: str = None, max_results: int = 10) -> list[dict]:
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise ValueError("NEWSAPI_KEY not found in .env file")

    # Use our smart query builder instead of manually combining
    query = get_search_query(ticker)

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "apiKey": api_key,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])

    headlines = []
    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")
        if not title or title == "[Removed]":
            continue
        headlines.append({
            "title": title,
            "description": description or "",
            "full_text": f"{title}. {description}" if description else title,
            "url": article.get("url", ""),
            "published_at": article.get("publishedAt", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
        })

    return headlines

# A hardcoded mapping of common tickers to company names
# We'll use this so our searches are more accurate
TICKER_TO_COMPANY = {
    # ── US Tech ──────────────────────────────────────────────────────────────
    "AAPL":   "Apple",
    "GOOGL":  "Google Alphabet",
    "MSFT":   "Microsoft",
    "AMZN":   "Amazon",
    "META":   "Meta Facebook",
    "NVDA":   "Nvidia",
    "TSLA":   "Tesla",
    "NFLX":   "Netflix",
    "UBER":   "Uber",
    "LYFT":   "Lyft",
    "SNAP":   "Snapchat",
    "TWTR":   "Twitter X",
    "AMD":    "AMD chip semiconductor",
    "INTC":   "Intel",
    "ORCL":   "Oracle",
    "CRM":    "Salesforce",
    "ADBE":   "Adobe",
    "PYPL":   "PayPal",
    "SQ":     "Block Square payments",
    "SHOP":   "Shopify",
    "ZOOM":   "Zoom Video",
    "SPOT":   "Spotify",
    "COIN":   "Coinbase crypto",
    "PLTR":   "Palantir",
    "AI":     "C3.ai artificial intelligence",
    "OPENAI": "OpenAI ChatGPT",

    # ── US Finance ───────────────────────────────────────────────────────────
    "JPM":    "JPMorgan Chase bank",
    "GS":     "Goldman Sachs",
    "MS":     "Morgan Stanley",
    "BAC":    "Bank of America",
    "WFC":    "Wells Fargo",
    "V":      "Visa",
    "MA":     "Mastercard",

    # ── US Other ─────────────────────────────────────────────────────────────
    "TSMC":   "TSMC Taiwan semiconductor",
    "BRK":    "Berkshire Hathaway Buffett",
    "DIS":    "Disney",
    "BABA":   "Alibaba",
    "JNJ":    "Johnson Johnson",
    "PFE":    "Pfizer",
    "ELON":   "Elon Musk",

    # ── Indian IT ────────────────────────────────────────────────────────────
    "TCS":      "Tata Consultancy Services TCS",
    "INFY":     "Infosys",
    "WIPRO":    "Wipro",
    "HCL":      "HCL Technologies",
    "TECHM":    "Tech Mahindra",
    "LTIM":     "LTIMindtree",
    "MPHASIS":  "Mphasis",
    "COFORGE":  "Coforge",
    "PERSISTENT": "Persistent Systems",
    "KPIT":     "KPIT Technologies",

    # ── Indian Conglomerates ─────────────────────────────────────────────────
    "RELIANCE":  "Reliance Industries Mukesh Ambani",
    "TATA":      "Tata Group",
    "ADANI":     "Adani Group Gautam Adani",
    "BAJAJ":     "Bajaj Finance",
    "BIRLA":     "Aditya Birla Group",
    "MAHINDRA":  "Mahindra Group",

    # ── Indian Banks ─────────────────────────────────────────────────────────
    "HDFC":      "HDFC Bank",
    "ICICI":     "ICICI Bank",
    "SBI":       "State Bank of India SBI",
    "AXIS":      "Axis Bank",
    "KOTAK":     "Kotak Mahindra Bank",
    "INDUSIND":  "IndusInd Bank",
    "YESBANK":   "Yes Bank",
    "PNB":       "Punjab National Bank",

    # ── Indian Consumer + Auto ───────────────────────────────────────────────
    "MARUTI":    "Maruti Suzuki",
    "TATAMOTORS": "Tata Motors",
    "HEROMOTOCO": "Hero MotoCorp",
    "BAJAJATO":  "Bajaj Auto",
    "EICHER":    "Eicher Motors Royal Enfield",
    "ONGC":      "ONGC oil gas India",
    "NTPC":      "NTPC power India",
    "POWERGRID": "Power Grid India",
    "ITC":       "ITC cigarettes FMCG India",
    "HINDUNILVR": "Hindustan Unilever",
    "NESTLEIND": "Nestle India",
    "DABUR":     "Dabur India",

    # ── Indian Startups / New Age ────────────────────────────────────────────
    "ZOMATO":    "Zomato food delivery",
    "PAYTM":     "Paytm One97 Communications",
    "NYKAA":     "Nykaa FSN Ecommerce",
    "POLICYBZR": "PolicyBazaar PB Fintech",
    "DELHIVERY": "Delhivery logistics",
    "MAPMYINDIA": "MapmyIndia CE Info Systems",

    # ── Global ───────────────────────────────────────────────────────────────
    "SAMSUNG":   "Samsung Electronics",
    "SONY":      "Sony",
    "TOYOTA":    "Toyota",
    "VOLKSWAGEN": "Volkswagen",
    "HSBC":      "HSBC bank",
    "SOFTBANK":  "SoftBank",
    "BITCOIN":   "Bitcoin cryptocurrency",
    "ETHEREUM":  "Ethereum cryptocurrency",
}


def get_company_name(ticker: str) -> str | None:
    """
    Look up company name for a ticker.
    
    If not in our dictionary, we still return the ticker itself
    as a search term — NewsAPI will find relevant articles.
    Better than returning None and getting poor results.
    """
    return TICKER_TO_COMPANY.get(ticker.upper())


def get_search_query(ticker: str) -> str:
    """
    Build the best possible search query for a ticker.
    
    Known ticker  → "TSLA OR Tesla"          (ticker + company name)
    Unknown ticker → "WIPRO"                  (just the ticker — still works)
    """
    company = get_company_name(ticker.upper())
    if company:
        return f"{ticker} OR {company}"
    else:
        # Unknown ticker — search by ticker name only
        # NewsAPI is good enough to find relevant articles
        return ticker