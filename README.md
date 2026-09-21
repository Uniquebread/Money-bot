# Money Bot

Finds new referral bonuses, affiliate programs, crypto airdrops, cashback
offers, freelance gigs and general side-income opportunities from Reddit,
Google News and Product Hunt every 2 hours, and (optionally) from X, and
sends you a digest on **Telegram**. Also publishes a browsable archive as a
free website via GitHub Pages.

Runs entirely on GitHub's free infrastructure (GitHub Actions + GitHub
Pages) — **no server, no hosting bill, no code to keep running yourself.**

---

## What it does every run

1. Fetches new posts from Reddit (beermoney, passive_income, Airdrops,
   affiliatemarketing, WorkOnline, freelance, sidehustle, slavelabour,
   referralcodes, churning), Google News searches, and Product Hunt.
2. Scores each item against a keyword list and sorts it into a category
   (Crypto & Airdrops / Referral & Affiliate / Cashback & Sign-up Bonuses /
   Freelance & Gigs / General Side Income).
3. Drops anything it already reported to you before (dedupe store).
4. Sends whatever's new to you on Telegram.
5. Updates a website (GitHub Pages) with the latest digest + a dated
   archive of every past run.

X (Twitter) is wired in but **off by default** — see the cost section below
before turning it on.

---

## One-time setup (about 15 minutes)

### 1. Create a GitHub repo
Create a new **private** repo (recommended, since the archive and dedupe
store will live in it) and push these files to it.

```bash
cd money-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

### 2. Create your Telegram bot (free, ~2 minutes)
1. Open Telegram, search for **@BotFather**, start a chat.
2. Send `/newbot`, follow the prompts (choose a name and a username ending
   in `bot`). BotFather replies with a token like
   `123456789:AAExampleTokenHere123`. Copy it.
3. Search for your new bot by its username and send it any message (e.g.
   "hi"). This is required — Telegram won't let a bot message you first.
4. In a browser, visit (replace `<TOKEN>` with your token):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Find `"chat":{"id": ...}` in the JSON — that number is your chat ID.

### 3. Add secrets to your GitHub repo
Go to **Settings → Secrets and variables → Actions → New repository
secret** and add:

| Secret name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the token from BotFather |
| `TELEGRAM_CHAT_ID` | the chat id you looked up |

(Optional, only if you also want email as a backup channel — otherwise
skip these entirely and email just stays off:)

| Secret name | Value |
|---|---|
| `SMTP_USER` | your email address |
| `SMTP_PASS` | an app password (not your normal password — Gmail requires a generated "App Password") |
| `EMAIL_TO` | where to send the digest |
| `SMTP_HOST` | e.g. `smtp.gmail.com` (defaults to this if unset) |
| `SMTP_PORT` | e.g. `587` (defaults to this if unset) |

### 4. Allow the workflow to push commits
Go to **Settings → Actions → General → Workflow permissions** and select
**"Read and write permissions"**, then save. (This lets the bot commit the
updated website/archive back to the repo after every run.)

### 5. Turn on GitHub Pages
Go to **Settings → Pages**. Under "Build and deployment", set **Source** to
"Deploy from a branch", branch `main`, folder `/docs`. Save. GitHub gives
you a URL like `https://<your-username>.github.io/<your-repo>/` — that's
your live digest archive.

### 6. Run it
Go to the **Actions** tab, open "Money Bot Digest (every 2 hours)", click
**Run workflow** to fire it manually and confirm everything works. After
that, it runs automatically every 2 hours forever, for free.

---

## About X (Twitter) — read before enabling

**X has no free tier for reading data as of February 2026.** Every post a
search returns is billed (pay-per-use, roughly $0.005/post at the time this
was written — check https://docs.x.com/x-api/getting-started/pricing for
current rates, they've moved before). There is no way around this without
violating X's Terms of Service (scraping, logged-out automation, etc.),
which I've deliberately not built here since it gets IPs/accounts blocked
and isn't a stable foundation for a tool you rely on.

If you decide it's worth it:
1. Apply for a developer account at https://developer.x.com and set up
   pay-per-use billing with a **spending limit** (important — set this on
   day one so a bug can't run up a bill).
2. Add `TWITTER_BEARER_TOKEN` as a repo secret.
3. That's it — `x-digest.yml` already exists and runs **once a day**
   (not every 2 hours, to keep cost low) and is hard-capped at 20 posts
   read per run (~$0.10/day, ~$3/month) via `X_MAX_POSTS_PER_RUN` in
   `config.py`. Adjust the cron schedule or the cap if you want more —
   just know the cost scales linearly with posts read.

Until you add that secret, the X workflow runs on schedule but does
nothing and costs nothing (it detects the missing token and exits early).

---

## Tuning it

- **Keywords/categories:** edit `filter.py` — `KEYWORDS` dict. Add/remove
  terms freely; weights just influence sort order, not inclusion (anything
  matching at least one keyword is included).
- **Subreddits:** edit `SUBREDDITS` in `sources/reddit_rss.py`.
- **News search terms:** edit `QUERIES` in `sources/google_news_rss.py`.
- **Frequency:** edit the `cron` line in `.github/workflows/digest.yml`
  (currently `0 */2 * * *` = every 2 hours). Cron schedules are UTC.
- **How much history it keeps before re-showing an item:** `SEEN_RETENTION_DAYS`
  in `config.py` (default 30 days).

---

## Running it locally (optional, for testing)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
python main.py
```

Without the Telegram env vars set, it just prints what it would have sent
to the console instead of failing — safe to run without any secrets to
see what it finds.

---

## Project structure

```
money-bot/
├── main.py                  # orchestrator - run this
├── run_x_only.py            # entrypoint used by the daily X workflow
├── config.py                # all settings, reads from env vars
├── filter.py                # keyword scoring + categorization
├── store.py                 # dedupe store (data/seen.json)
├── digest.py                # builds Telegram text + website HTML
├── sources/
│   ├── reddit_rss.py
│   ├── google_news_rss.py
│   ├── producthunt_rss.py
│   └── x_api.py             # optional, costs money, off by default
├── notifiers/
│   ├── telegram_notifier.py # primary channel
│   └── emailer.py           # optional secondary channel, off by default
├── docs/                    # generated website (served by GitHub Pages)
├── data/seen.json           # generated dedupe store
└── .github/workflows/
    ├── digest.yml           # every 2 hours, free sources
    └── x-digest.yml         # once daily, X only, costs money if enabled
```
