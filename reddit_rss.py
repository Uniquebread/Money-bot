"""
Pulls new posts from a curated list of money-opportunity-focused subreddits
using Reddit's public .rss feeds. No API key or login required.
"""
import feedparser
import requests

SUBREDDITS = [
    "beermoney",
    "passive_income",
    "Airdrops",
    "affiliatemarketing",
    "WorkOnline",
    "freelance",
    "sidehustle",
    "slavelabour",
    "referralcodes",
    "churning",  # credit card / bank sign-up bonuses
]

HEADERS = {
    # Reddit blocks requests with no / generic user-agent.
    "User-Agent": "money-bot/1.0 (personal research digest; contact: none)"
}


def fetch():
    items = []
    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/new/.rss?limit=25"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"[reddit_rss] failed for r/{sub}: {e}")
            continue

        for entry in feed.entries:
            items.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "snippet": _clean_summary(entry.get("summary", "")),
                "source": f"Reddit r/{sub}",
                "published": entry.get("published", ""),
            })
    return items


def _clean_summary(html_summary, max_len=280):
    import re
    text = re.sub("<[^<]+?>", " ", html_summary or "")
    text = " ".join(text.split())
    return text[:max_len]
