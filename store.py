"""
Tracks which items have already been reported so the same referral post /
airdrop / article doesn't get sent to you again every 2 hours. Backed by a
plain JSON file that the GitHub Actions workflow commits back to the repo
after every run, so state persists between runs even though each run is a
fresh container.
"""
import json
import os
import time
import hashlib

import config


def _hash(link):
    return hashlib.sha256(link.encode("utf-8")).hexdigest()


def load():
    if not os.path.exists(config.SEEN_STORE_PATH):
        return {}
    try:
        with open(config.SEEN_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save(seen):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.SEEN_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2)


def prune(seen):
    """Drop entries older than SEEN_RETENTION_DAYS so the file doesn't grow forever."""
    cutoff = time.time() - (config.SEEN_RETENTION_DAYS * 86400)
    return {h: ts for h, ts in seen.items() if ts >= cutoff}


def split_new_items(items, seen):
    """
    Returns (new_items, updated_seen_dict). new_items are the ones not in
    `seen` (by hash of their link); updated_seen_dict has them added with
    the current timestamp.
    """
    new_items = []
    now = time.time()
    for item in items:
        h = _hash(item["link"])
        if h not in seen:
            seen[h] = now
            new_items.append(item)
    return new_items, seen
