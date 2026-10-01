"""
Pulls recent posts from PUBLIC Telegram channels using Telegram's own
public web preview (t.me/s/<channel>), which requires no API key, no
login, and no bot setup - it's the same page Google indexes.

IMPORTANT - curate this list yourself: the airdrop/opportunity Telegram
space is heavily targeted by scam and impersonator channels. Verify any
channel yourself before trusting what it posts, and before adding more.

Non-English posts are auto-translated (free, no API key - see
translate.py). If the translation endpoint starts rate-limiting us
partway through a run, we stop attempting further translations for the
REST of this run and just use original-language text instead, rather
than burning the time budget on calls that are going to fail anyway.

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

MAX_POSTS_PER_CHANNEL = 12
MAX_CONSECUTIVE_TRANSLATE_FAILURES = 2


def fetch():
    items = []
    consecutive_translate_failures = 0
    translation_disabled_this_run = False

    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
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

            source_label = f"Telegram @{channel}"
            if translation_disabled_this_run:
                text, detected_lang = raw_text, "unknown"
            else:
                text, detected_lang = translate.translate_to_english(raw_text, timeout=6)
                if detected_lang == "unknown":
                    consecutive_translate_failures += 1
                    if consecutive_translate_failures >= MAX_CONSECUTIVE_TRANSLATE_FAILURES:
                        translation_disabled_this_run = True
                        print(
                            f"[telegram_channels] translation failing repeatedly - "
                            f"disabling it for the rest of this run."
                        )
                else:
                    consecutive_translate_failures = 0
                    if detected_lang != "en":
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
