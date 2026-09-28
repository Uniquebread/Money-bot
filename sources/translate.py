"""
Free, no-API-key translation for non-English source posts.

Uses Google Translate's public web endpoint - free, no signup, but
unofficial. If it ever breaks, translate_to_english() fails safe and
just returns the original text rather than crashing the bot.
"""
import requests

_ENDPOINT = "https://translate.googleapis.com/translate_a/single"


def _looks_non_latin(text):
    for ch in text:
        if ord(ch) > 0x2AF:
            return True
    return False


def translate_to_english(text, timeout=10):
    if not text or not text.strip():
        return text, "en"

    if not _looks_non_latin(text):
        return text, "en"

    try:
        resp = requests.get(
            _ENDPOINT,
            params={"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text[:500]},
            headers={"User-Agent": "Mozilla/5.0 (compatible; money-bot/1.0)"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        translated = "".join(seg[0] for seg in data[0] if seg[0])
        detected_lang = data[2] if len(data) > 2 else "unknown"
        return translated or text, detected_lang
    except Exception as e:
        print(f"[translate] failed, using original text: {e}")
        return text, "unknown"
