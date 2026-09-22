"""
Central config. Everything here is read from environment variables so that
no secrets ever live in the code itself. In GitHub Actions these are supplied
via `secrets.*` in the workflow file (see .github/workflows/digest.yml).
"""
import os

# --- Telegram (primary delivery channel) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- Email (optional secondary channel - off unless SMTP secrets are set) ---
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT") or "587") 
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Money Bot")

# --- X / Twitter (optional, COSTS MONEY - see sources/x_api.py) ---
# X removed its free read tier in Feb 2026. Reads are billed per-post at
# the official pay-per-use rate. This is OFF by default (empty token = the
# X source silently skips itself). Only set this if you've accepted the
# cost. Because of the per-read cost, X is deliberately polled far less
# often than everything else - see the separate "x-digest" workflow,
# which defaults to once per day instead of every 2 hours.
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")
# Hard safety cap: max posts pulled from X per run, regardless of query
# count, so a bug can't silently rack up a large bill.
X_MAX_POSTS_PER_RUN = int(os.environ.get("X_MAX_POSTS_PER_RUN", "20"))

# --- Behaviour ---
# How many days to keep an item in the "seen" store before it can be
# reported again if it resurfaces (keeps the store file from growing forever).
SEEN_RETENTION_DAYS = 30

# Minimum keyword-relevance score for an item to be included in the digest.
MIN_SCORE = 1

# Max items per digest email / page refresh, per category.
MAX_ITEMS_PER_CATEGORY = 12

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SEEN_STORE_PATH = os.path.join(DATA_DIR, "seen.json")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "archive")
