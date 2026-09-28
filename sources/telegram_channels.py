"""
Pulls recent posts from PUBLIC Telegram channels using Telegram's own
public web preview (t.me/s/<channel>), which requires no API key, no
login, and no bot setup - it's the same page Google indexes.

IMPORTANT - curate this list yourself: the airdrop/opportunity Telegram
space is heavily targeted by scam and impersonator channels. Verify any
channel yourself before trusting what it posts, and before adding more.

Non-English posts are automatically translated to English (best-effort,
free, no API key - see translate.py).

To add a channel: find its public link, e.g. t.me/somechannel, and add
"somechannel" (no @, no t.me/) to the CHANNELS list below.
"""
from bs4 import BeautifulSoup
import requests

import translate

CHANNELS = [
    "airdropalert",
    "airdropfind",
    "airdropminders",
    "VerifyAirdropg",
    "airdrop_hunter_public",
    # Add more usernames here, one per line, e.g.:
    # "your_trusted_channel",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; money-bot/1.0)"}

MAX_POSTS_PER_CHANNEL = 20


def fetch():
    items = []
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"[telegram_channels] failed for {channel}: {e}")
            continue

        messages = soup.find_all("div", class_="tgme_widget_message", attrs={"data-post": True})

        for msg in messages[-MAX_POSTS_PER_CHANNEL:]:
            post_id = msg.get("data-post", "")
            text_div = msg.find("div", class_="tgme_widget_message_text")
            if not text_div:
                continue
            raw_text = text_div.get_text(separator=" ", strip=True)
            if not raw_text:
                continue

            text, detected_lang = translate.translate_to_english(raw_text)
            source_label = f"Telegram @{channel}"
            if detected_lang not in ("en", "unknown"):
                source_label += f" (translated from {detected_lang})"

            time_tag = msg.find("time")
            published = time_tag.get("datetime", "") if time_tag else ""

            items.append({
                "title": text[:120],
                "link": f"https://t.me/{post_id}",
                "snippet": text[:280],
                "source": source_label,
                "published": published,
            })
    return items
