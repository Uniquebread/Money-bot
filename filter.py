"""
Scores each item for relevance to "money-making opportunities" and buckets
it into a category for a more readable digest. Pure keyword matching - no
external dependency, fast, and easy for you to tune the KEYWORDS dict below.
"""
import re

# category -> list of (keyword, weight)
KEYWORDS = {
    "Crypto & Airdrops": [
        ("airdrop", 3), ("testnet", 2), ("staking reward", 3),
        ("token launch", 2), ("presale", 2), ("whitelist", 1),
        ("claim your", 2), ("crypto", 1),
    ],
    "Referral & Affiliate": [
        ("referral bonus", 3), ("refer a friend", 3), ("affiliate program", 3),
        ("commission", 1), ("referral code", 2), ("invite friends", 2),
        ("affiliate", 1),
    ],
    "Cashback & Sign-up Bonuses": [
        ("cashback", 2), ("sign-up bonus", 3), ("signup bonus", 3),
        ("welcome bonus", 2), ("bank bonus", 2), ("credit card bonus", 2),
    ],
    "Freelance & Gigs": [
        ("freelance", 2), ("remote job", 2), ("gig", 1), ("hire me", 1),
        ("hiring", 1), ("work from home", 2), ("part-time income", 2),
    ],
    "General Side Income": [
        ("side hustle", 3), ("passive income", 3), ("make money", 2),
        ("earn extra", 2), ("get paid", 1), ("giveaway", 1),
        ("free money", 2), ("extra income", 2),
    ],
}

# Flatten for fast scoring
_ALL_KEYWORDS = [
    (cat, kw, weight)
    for cat, kws in KEYWORDS.items()
    for kw, weight in kws
]


def score_and_categorize(item):
    """
    Returns (score, category) for an item dict with 'title' and 'snippet'.
    category is the KEYWORDS bucket with the highest matched weight;
    falls back to 'General Side Income' if nothing matches but score > 0
    is still required for inclusion (checked by caller).
    """
    text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
    cat_scores = {cat: 0 for cat in KEYWORDS}

    for cat, kw, weight in _ALL_KEYWORDS:
        if kw in text:
            cat_scores[cat] += weight

    best_cat = max(cat_scores, key=cat_scores.get)
    total_score = sum(cat_scores.values())
    return total_score, best_cat if cat_scores[best_cat] > 0 else "General Side Income"


def filter_items(items, min_score=1):
    """Scores every item, drops low-relevance ones, attaches score/category."""
    out = []
    for item in items:
        score, category = score_and_categorize(item)
        if score >= min_score:
            item = dict(item)
            item["score"] = score
            item["category"] = category
            out.append(item)
    out.sort(key=lambda x: x["score"], reverse=True)
    return out
