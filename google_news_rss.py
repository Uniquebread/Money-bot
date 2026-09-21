"""
Pulls recent news matching money-opportunity search queries via Google
News' public RSS search endpoint. No API key required.
"""
import feedparser
import requests
from urllib.parse import quote_plus

QUERIES = [
    "referral bonus program",
    "crypto airdrop",
    "new affiliate program launch",
    "sign-up bonus offer",
    "side hustle 2026",
    "cashback promotion",
    "refer a friend reward",
    "passive income opportunity",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; money-bot/1.0)"}


def fetch():
    items = []
    for query in QUERIES:
        url = (
            "https://news.google.com/rss/search?q="
            f"{quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"[google_news_rss] failed for '{query}': {e}")
            continue

        for entry in feed.entries[:15]:
            items.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "snippet": entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else "",
                "source": "Google News",
                "published": entry.get("published", ""),
            })
    return items
