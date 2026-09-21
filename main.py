"""
Orchestrates one full run of the bot:
  1. Fetch from every source
  2. Score + categorize + filter for relevance
  3. Drop anything already seen (dedupe store)
  4. Build the Telegram message + website page
  5. Send to Telegram (and email, if configured)
  6. Write the website files and update the dedupe store on disk

Run manually with:  python main.py
The GitHub Actions workflows call this exact script on a schedule.
"""
import os
import sys
from datetime import datetime, timezone

import config
import store
import filter as relevance_filter
import digest
from notifiers import telegram_notifier, emailer

from sources import reddit_rss, google_news_rss, producthunt_rss, x_api

# Sources that are always free to poll frequently.
FREE_SOURCES = [reddit_rss, google_news_rss, producthunt_rss]

# X is separate because it costs money per read - see sources/x_api.py.
# Controlled by the RUN_X_SOURCE env var so the every-2-hours workflow can
# leave it off and a separate, less frequent workflow can turn it on.
RUN_X_SOURCE = os.environ.get("RUN_X_SOURCE", "false").lower() == "true"


def run():
    run_time = datetime.now(timezone.utc)
    print(f"=== Money Bot run started {run_time.isoformat()} ===")

    all_items = []
    for source_module in FREE_SOURCES:
        name = source_module.__name__
        try:
            fetched = source_module.fetch()
            print(f"[{name}] fetched {len(fetched)} items")
            all_items.extend(fetched)
        except Exception as e:
            print(f"[{name}] FAILED: {e}")

    if RUN_X_SOURCE:
        try:
            fetched = x_api.fetch()
            print(f"[x_api] fetched {len(fetched)} items")
            all_items.extend(fetched)
        except Exception as e:
            print(f"[x_api] FAILED: {e}")
    else:
        print("[x_api] RUN_X_SOURCE is not 'true' - skipping (no cost incurred).")

    print(f"Total raw items fetched: {len(all_items)}")

    # Drop items with no link/title (malformed feed entries)
    all_items = [it for it in all_items if it.get("link") and it.get("title")]

    # Score + filter for relevance
    relevant = relevance_filter.filter_items(all_items, min_score=config.MIN_SCORE)
    print(f"Relevant after keyword filter: {len(relevant)}")

    # Dedupe against what's already been reported
    seen = store.load()
    seen = store.prune(seen)
    new_items, seen = store.split_new_items(relevant, seen)
    print(f"New (not previously seen): {len(new_items)}")

    # Build outputs
    telegram_text = digest.build_telegram_message(new_items, run_time)
    website_html = digest.build_website_page(new_items, run_time, page_title="Latest Digest")

    # Send
    telegram_notifier.send(telegram_text)
    email_html = digest.build_website_page(new_items, run_time, page_title="Email Digest")
    emailer.send(f"Money Bot Digest - {run_time.strftime('%Y-%m-%d %H:%M UTC')}", email_html)

    # Persist website (index + dated archive copy) and dedupe store
    os.makedirs(config.DOCS_DIR, exist_ok=True)
    os.makedirs(config.ARCHIVE_DIR, exist_ok=True)

    with open(os.path.join(config.DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(website_html)

    archive_name = run_time.strftime("%Y-%m-%d_%H%M") + ".html"
    with open(os.path.join(config.ARCHIVE_DIR, archive_name), "w", encoding="utf-8") as f:
        f.write(website_html)

    _update_archive_index()

    store.save(seen)

    print(f"=== Run complete. {len(new_items)} new item(s) reported. ===")


def _update_archive_index():
    """Regenerates a simple index of archive/*.html for browsing past runs."""
    files = sorted(
        (f for f in os.listdir(config.ARCHIVE_DIR) if f.endswith(".html")),
        reverse=True,
    )
    links = "\n".join(f'<li><a href="{f}">{f.replace(".html", "").replace("_", " ")}</a></li>' for f in files)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Archive - Money Bot</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 780px;
         margin: 0 auto; padding: 24px 16px; background: #0b1210; color: #eee; }}
  a {{ color: #f0c419; }}
  li {{ margin-bottom: 6px; }}
</style></head>
<body>
<p><a href="../index.html">&larr; Back to latest</a></p>
<h1>Digest Archive</h1>
<ul>{links}</ul>
</body></html>"""
    with open(os.path.join(config.ARCHIVE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        raise
