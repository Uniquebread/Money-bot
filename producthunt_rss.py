"""
Pulls newly launched products from Product Hunt's public RSS feed.
New launches frequently come with early affiliate/referral programs or
limited-time deals, which is why this is useful signal for "opportunities".
"""
import feedparser
import requests

FEED_URL = "https://www.producthunt.com/feed"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; money-bot/1.0)"}


def fetch():
    items = []
    try:
        resp = requests.get(FEED_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"[producthunt_rss] failed: {e}")
        return items

    for entry in feed.entries[:25]:
        items.append({
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", "").strip(),
            "snippet": entry.get("summary", "")[:280],
            "source": "Product Hunt",
            "published": entry.get("published", ""),
        })
    return items
