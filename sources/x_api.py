"""
Pulls recent posts from X (Twitter) via the OFFICIAL v2 API.

This deliberately does NOT scrape X. Scraping X (via unofficial libraries,
logged-out browser automation, Nitter mirrors, etc.) violates X's Terms of
Service and gets IPs / accounts blocked quickly and unpredictably. The only
supported path here is the real API, which requires a developer account and
a bearer token.

COST WARNING: as of Feb 2026, X has no free read tier. Every post returned
by search is billed (pay-per-use, ~$0.005/post at time of writing - check
https://docs.x.com/x-api/getting-started/pricing for current rates). This
module enforces config.X_MAX_POSTS_PER_RUN as a hard ceiling so a bug or a
noisy query set can't silently run up a bill.

If TWITTER_BEARER_TOKEN is not set, this source silently returns nothing so
the rest of the bot still runs fine off the free sources. Because of the
per-read cost, this is wired to a separate, much-less-frequent workflow
(default: once a day, not every 2 hours) - see .github/workflows/x-digest.yml.

Docs: https://developer.x.com/en/docs/x-api/tweets/search/api-reference/get-tweets-search-recent
"""
import requests
import config

SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

# Keep this list short and high-signal - each result costs money. Trim or
# reorder freely; the fetch loop stops early once X_MAX_POSTS_PER_RUN is hit.
QUERIES = [
    '"referral bonus" -is:retweet lang:en',
    '"airdrop" crypto -is:retweet lang:en',
    '"affiliate program" launch -is:retweet lang:en',
    '"side hustle" opportunity -is:retweet lang:en',
]

# Kept small on purpose - see COST WARNING above.
RESULTS_PER_QUERY = 10


def fetch():
    items = []
    if not config.TWITTER_BEARER_TOKEN:
        print("[x_api] no TWITTER_BEARER_TOKEN set - skipping X source (no cost incurred).")
        return items

    headers = {"Authorization": f"Bearer {config.TWITTER_BEARER_TOKEN}"}
    budget = config.X_MAX_POSTS_PER_RUN

    for query in QUERIES:
        if budget <= 0:
            print("[x_api] per-run post budget reached, stopping early.")
            break

        params = {
            "query": query,
            "max_results": min(RESULTS_PER_QUERY, max(10, budget)),  # API min is 10
            "tweet.fields": "created_at,author_id,public_metrics",
        }
        try:
            resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=15)
            if resp.status_code == 429:
                print("[x_api] rate limited, stopping X fetch for this run.")
                break
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[x_api] failed for query '{query}': {e}")
            continue

        results = data.get("data", [])
        for tweet in results:
            if budget <= 0:
                break
            tweet_id = tweet["id"]
            items.append({
                "title": tweet["text"][:120].replace("\n", " "),
                "link": f"https://x.com/i/web/status/{tweet_id}",
                "snippet": tweet["text"][:280].replace("\n", " "),
                "source": "X (Twitter)",
                "published": tweet.get("created_at", ""),
            })
            budget -= 1

    print(f"[x_api] pulled {len(items)} posts this run (~${len(items)*0.005:.3f} estimated cost).")
    return items
