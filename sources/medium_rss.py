"""
Pulls recent Medium articles by tag via Medium's public per-tag RSS feeds.
"""
import re
import feedparser
import requests

TAGS = [
    "side-hustle",
    "passive-income",
    "make-money-online",
    "affiliate-marketing",
    "airdrop",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; money-bot/1.0)"}


def fetch():
    items = []
    for tag in TAGS:
        url = f"https://medium.com/feed/tag/{tag}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"[medium_rss] failed for tag '{tag}': {e}")
            continue

        for entry in feed.entries[:15]:
            summary = entry.get("summary", "")
            clean_summary = re.sub("<[^<]+?>", " ", summary)
            clean_summary = " ".join(clean_summary.split())[:280]

            items.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "snippet": clean_summary,
                "source": f"Medium (#{tag})",
                "published": entry.get("published", ""),
            })
    return items
