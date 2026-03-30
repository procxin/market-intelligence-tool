"""
Market Intelligence Tool — Scoring Engine
=================================
Keyword-based sentiment and impact scoring for news/events.
"""

from __future__ import annotations
import re

# ── Keyword Impact Weights ──────────────────────────────────
HIGH_IMPACT_KEYWORDS = {
    # Monetary policy
    "rate hike": 8, "rate cut": 8, "quantitative easing": 7, "quantitative tightening": 7,
    "fed pivot": 9, "fomc": 7, "hawkish": 6, "dovish": 6, "tapering": 7,
    "balance sheet": 5, "emergency meeting": 9, "liquidity crisis": 9,
    # Macro shocks
    "recession": 8, "stagflation": 7, "inflation surge": 7, "deflation": 7,
    "bank run": 9, "banking crisis": 9, "credit crunch": 8, "default": 8,
    "debt ceiling": 7, "government shutdown": 6, "fiscal cliff": 7,
    # Geopolitical
    "war": 9, "invasion": 9, "sanctions": 7, "embargo": 7, "nuclear": 9,
    "missile": 8, "escalation": 7, "ceasefire": 6, "peace deal": 6,
    "trade war": 7, "tariff": 6, "blockade": 8,
    # Market structure
    "margin call": 8, "liquidation": 7, "circuit breaker": 9, "flash crash": 9,
    "short squeeze": 7, "black swan": 9, "contagion": 8, "systemic risk": 8,
    # Corporate
    "bankruptcy": 8, "acquisition": 6, "merger": 6, "ipo": 5, "buyback": 5,
    "guidance raise": 6, "guidance cut": 7, "profit warning": 7, "fraud": 8,
    "lawsuit": 5, "activist investor": 6, "ceo resign": 7,
    # Crypto specific
    "hack": 7, "exploit": 7, "rug pull": 8, "stablecoin depeg": 9,
    "etf approval": 8, "etf rejection": 7, "regulation": 6,
}

POSITIVE_WORDS = {
    "surge", "rally", "soar", "jump", "gain", "bullish", "breakout",
    "recovery", "upgrade", "beat", "outperform", "record high", "growth",
    "optimism", "boom", "expansion", "approval", "breakthrough",
}

NEGATIVE_WORDS = {
    "crash", "plunge", "sink", "tumble", "collapse", "bearish", "breakdown",
    "selloff", "sell-off", "downgrade", "miss", "underperform", "record low",
    "fear", "bust", "contraction", "rejection", "failure", "crisis", "panic",
}


def score_impact(text: str) -> int:
    """Score text for market impact (0-10 scale)."""
    text_lower = text.lower()
    max_score = 0
    for keyword, weight in HIGH_IMPACT_KEYWORDS.items():
        if keyword in text_lower:
            max_score = max(max_score, weight)
    return min(max_score, 10)


def score_sentiment(text: str) -> float:
    """Simple sentiment score: -1.0 (bearish) to +1.0 (bullish)."""
    text_lower = text.lower()
    pos_count = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total


def impact_label(score: int) -> str:
    if score >= 8:
        return "🔴 Critical"
    elif score >= 6:
        return "🟠 High"
    elif score >= 4:
        return "🟡 Medium"
    elif score >= 2:
        return "🔵 Low"
    return "⚪ Minimal"


def sentiment_label(score: float) -> str:
    if score > 0.3:
        return "🟢 Bullish"
    elif score < -0.3:
        return "🔴 Bearish"
    return "⚪ Neutral"


def keyword_matches(text: str, keywords: list[str]) -> list[str]:
    """Find which keywords from a list appear in the text."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]
