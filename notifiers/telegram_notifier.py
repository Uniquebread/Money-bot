"""
Sends the digest to you via Telegram (free Bot API, no per-message cost,
no inbox clutter). Setup (one-time, ~2 minutes):

1. Open Telegram, message @BotFather, send /newbot, follow the prompts.
   BotFather gives you a token like "123456789:AAExampleTokenHere".
2. Message your new bot anything (e.g. "hi") so it's allowed to message
   you back.
3. Get your chat_id: visit
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   in a browser right after step 2 - your chat id is in the JSON response
   under result[0].message.chat.id.
4. Put the token and chat id into GitHub repo secrets as
   TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (see README.md).

Telegram messages are capped at 4096 characters, so long digests are split
into multiple messages automatically.
"""
import requests
import config

API_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4000  # a little under Telegram's 4096 hard cap, for safety margin


def _chunk(text, max_len=MAX_LEN):
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n\n", 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


def send(text):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[telegram_notifier] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set - skipping send.")
        print("---- Digest that would have been sent ----")
        print(text)
        return False

    url = API_URL_TEMPLATE.format(token=config.TELEGRAM_BOT_TOKEN)
    ok = True
    for chunk in _chunk(text):
        try:
            resp = requests.post(
                url,
                data={
                    "chat_id": config.TELEGRAM_CHAT_ID,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"[telegram_notifier] send failed: {resp.status_code} {resp.text}")
                ok = False
        except Exception as e:
            print(f"[telegram_notifier] send failed: {e}")
            ok = False
    return ok
