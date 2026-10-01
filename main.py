"""
Orchestrates one full run of the bot.
Run manually with:  python -u main.py
"""
import os
import re
import sys
import concurrent.futures
from datetime import datetime, timezone

import config
import store
import filter as relevance_filter
import digest
from notifiers import telegram_notifier, emailer

from sources import reddit_rss, google_news_rss, producthunt_rss, telegram_channels, medium_rss

SOURCES = [reddit_rss, google_news_rss, producthunt_rss, telegram_channels, medium_rss]

SOURCE_TIMEOUTS = {
    "sources.telegram_channels": 55,
}
DEFAULT_SOURCE_TIMEOUT_SECONDS = 25


def fetch_with_timeout(source_module):
    name = getattr(source_module, "__name__", str(source_module))
    timeout = SOURCE_TIMEOUTS.get(name, DEFAULT_SOURCE_TIMEOUT_SECONDS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(source_module.fetch)
        try:
            result = future.result(timeout=timeout)
            print(f"[{name}] fetched {len(result)} items", flush=True)
            return result
        except concurrent.futures.TimeoutError:
            print(f"[{name}] TIMED OUT after {timeout}s - skipping this run.", flush=True)
            return []
        except Exception as e:
            print(f"[{name}] FAILED: {e}", flush=True)
            return []


def _normalize_title(title):
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def dedupe_within_run(items):
    seen_titles = set()
    out = []
    dropped = 0
    for item in items:
        norm = _normalize_title(item.get("title", ""))
        if norm and norm in seen_titles:
            dropped += 1
            continue
        if norm:
            seen_titles.add(norm)
        out.append(item)
    if dropped:
        print(f"Removed {dropped} duplicate-title item(s) within this run", flush=True)
    return out


def run():
    run_time = datetime.now(timezone.utc)
    print(f"=== Money Bot run started {run_time.isoformat()} ===", flush=True)

    all_items = []
    for source_module in SOURCES:
        all_items.extend(fetch_with_timeout(source_module))

    scanned_count = len(all_items)
    print(f"Total raw items scanned: {scanned_count}", flush=True)

    all_items = [it for it in all_items if it.get("link") and it.get("title")]
    all_items = dedupe_within_run(all_items)

    relevant = relevance_filter.filter_items(all_items, min_score=config.MIN_SCORE)
    print(f"Passed strict genuine-opportunity filter: {len(relevant)} of {scanned_count} scanned", flush=True)

    seen = store.load()
    seen = store.prune(seen)
    new_items, seen = store.split_new_items(relevant, seen)
    print(f"New (not previously reported): {len(new_items)}", flush=True)

    telegram_text = digest.build_telegram_message(new_items, run_time, scanned_count=scanned_count)
    website_html = digest.build_website_page(new_items, run_time, page_title="Latest Digest")

    telegram_notifier.send(telegram_text)
    email_html = digest.build_website_page(new_items, run_time, page_title="Email Digest")
    emailer.send(f"Money Bot Digest - {run_time.strftime('%Y-%m-%d %H:%M UTC')}", email_html)

    os.makedirs(config.DOCS_DIR, exist_ok=True)
    os.makedirs(config.ARCHIVE_DIR, exist_ok=True)

    with open(os.path.join(config.DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(website_html)

    archive_name = run_time.strftime("%Y-%m-%d_%H%M") + ".html"
    with open(os.path.join(config.ARCHIVE_DIR, archive_name), "w", encoding="utf-8") as f:
        f.write(website_html)

    _update_archive_index()
    store.save(seen)

    print(f"=== Run complete. {len(new_items)} new item(s) reported. ===", flush=True)


def _update_archive_index():
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
        print(f"FATAL: {e}", file=sys.stderr, flush=True)
        raise
