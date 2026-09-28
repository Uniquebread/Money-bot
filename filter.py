"""
Scores each item for whether it's a genuine, ACTIONABLE opportunity that
someone is actually earning from - not just "mentions a related word,"
not a discussion/question post, and not betting/gambling.

No single approach without an LLM will be perfect - treat this as a
much stronger noise filter, not a scam guarantee. Always verify manually
before connecting a wallet, sending funds, or entering sensitive info
anywhere a "genuine" item points you.
"""
import re

CATEGORY_KEYWORDS = {
    "Crypto & Airdrops": ["airdrop", "testnet", "token", "presale", "whitelist", "crypto", "wallet"],
    "Referral & Affiliate": ["referral", "affiliate", "invite", "commission", "refer a friend"],
    "Cashback & Sign-up Bonuses": ["cashback", "sign-up bonus", "signup bonus", "welcome bonus", "bank bonus"],
    "Freelance & Gigs": ["freelance", "remote job", "gig", "hiring", "work from home"],
    "General Side Income": ["side hustle", "passive income", "make money", "extra income"],
}

ACTION_PHRASES = [
    "use code", "use my code", "referral code", "promo code",
    "sign up with", "sign up using", "claim your", "claim now",
    "trade $", "get $", "earn $", "instantly", "airdrop is live",
    "airdrop live", "whitelist is open", "whitelist open",
    "testnet reward", "limited spots", "first come first serve",
    "deposit bonus", "welcome bonus of", "cashback of",
]

EARNING_PROOF_PHRASES = [
    "i earned", "i made $", "i got paid", "i received", "just received",
    "just got paid", "cashed out", "payout received", "earned $",
    "made an extra $", "verified payment", "payment proof", "withdrawal proof",
    "successfully withdrew", "finally showing on my", "hit my account",
    "landed in my wallet",
]

WEAK_SIGNALS = [
    "airdrop", "referral", "affiliate", "cashback", "bonus", "giveaway",
    "side hustle", "passive income", "commission", "freelance", "remote job",
]

_MONEY_OR_PERCENT_RE = re.compile(r"(\$\s?\d|\d+\s?%|\d+\s?(usd|usdt|usdc))", re.IGNORECASE)

SCAM_SIGNALS = [
    "seed phrase", "private key", "send your wallet password",
    "double your", "guaranteed profit", "guaranteed return",
    "send eth to receive", "send btc to receive", "send crypto to receive",
    "dm me for", "dm to claim", "act now or lose", "verify your wallet by sending",
    "connect wallet to claim your prize", "you have been selected to receive",
    "congratulations you won", "limited slots dm now",
]

EXCLUDED_TOPICS = [
    "sportsbook", "sports betting", "bet now", "free bet", "odds boost",
    "bookmaker", "betting app", "betting site", "casino bonus", "parlay",
    "wager", "moneyline", "point spread", "bet slip", "betting odds",
    "gambling app", "online casino", "casino",
    "bonus bets", "bet $", "bet365", "draftkings", "fanduel", "betmgm",
    "caesars sportsbook", "fanatics sportsbook", "espn bet",
    "kalshi", "polymarket", "prediction market",
]

SOURCE_ACTIONABILITY_WEIGHT = {
    "reddit": 1.0,
    "telegram": 1.0,
    "producthunt": 0.8,
    "medium": 0.5,
    "google news": 0.3,
}


def _source_weight(source):
    s = source.lower()
    for key, weight in SOURCE_ACTIONABILITY_WEIGHT.items():
        if key in s:
            return weight
    return 0.5


def score_and_categorize(item):
    title = item.get("title", "")
    text = f"{title} {item.get('snippet', '')}".lower()

    action_hits = sum(1 for phrase in ACTION_PHRASES if phrase in text)
    proof_hits = sum(1 for phrase in EARNING_PROOF_PHRASES if phrase in text)
    weak_hits = sum(1 for word in WEAK_SIGNALS if word in text)
    scam_hits = sum(1 for phrase in SCAM_SIGNALS if phrase in text)
    excluded_hits = sum(1 for phrase in EXCLUDED_TOPICS if phrase in text)
    has_amount = bool(_MONEY_OR_PERCENT_RE.search(text))
    is_question = title.strip().endswith("?")

    raw_score = (
        (action_hits * 3)
        + (proof_hits * 4)
        + (weak_hits * 1)
        + (2 if has_amount else 0)
    )
    raw_score *= _source_weight(item.get("source", ""))
    raw_score -= scam_hits * 5
    if is_question:
        raw_score -= 2

    cat_scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        cat_scores[cat] = sum(1 for kw in kws if kw in text)
    best_cat = max(cat_scores, key=cat_scores.get)
    category = best_cat if cat_scores[best_cat] > 0 else "General Side Income"

    should_drop = (scam_hits > 0) or (excluded_hits > 0)
    return raw_score, category, should_drop


def filter_items(items, min_score=4):
    out = []
    for item in items:
        score, category, should_drop = score_and_categorize(item)
        if should_drop:
            continue
        if score >= min_score:
            item = dict(item)
            item["score"] = round(score, 1)
            item["category"] = category
            out.append(item)
    out.sort(key=lambda x: x["score"], reverse=True)
    return out
