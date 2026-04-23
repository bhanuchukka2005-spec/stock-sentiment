# test_news.py
from news import fetch_headlines, get_company_name

ticker = "TSLA"
company = get_company_name(ticker)

print(f"Fetching headlines for {ticker} ({company})...\n")

headlines = fetch_headlines(ticker, company, max_results=5)

print(f"Got {len(headlines)} headlines:\n")
for i, h in enumerate(headlines, 1):
    print(f"{i}. [{h['source']}] {h['title']}")
    print(f"   Published: {h['published_at']}")
    print()