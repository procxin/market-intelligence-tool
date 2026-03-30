"""
Market Intelligence Tool — News & Sentiment Engine
===========================================
Aggregated, scored, filtered news feed.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from data.cache import cached_fetch, source_watermark
from data.api_clients import get_news_feed
from components.cards import section_header, metric_card, empty_state
from components.charts import bar_chart
from theme import Palette
from utils.scoring import score_impact, score_sentiment, impact_label, sentiment_label
from utils.formatting import fmt_time_ago


def render():
    section_header("News & Sentiment Engine", "AI-scored, deduplicated news ranked by market impact", "📰")

    tabs = st.tabs(["Live Feed", "By Impact", "Sentiment Analysis", "Catalyst Watchlist"])

    # ── Load news ────────────────────────────────────
    with st.spinner("Aggregating news sources..."):
        result = cached_fetch("news_main_feed", lambda: get_news_feed(limit=50), mem_ttl=300, source="news")
        if isinstance(result, tuple):
            all_news, source = result
        elif isinstance(result, list):
            all_news, source = result, "cached"
        else:
            all_news, source = [], "none"

    scored_news = []
    for article in (all_news or []):
        title = article.get("title", "")
        text = article.get("text", "")
        combined = f"{title} {text}"
        article["impact_score"] = score_impact(combined)
        article["sentiment_score"] = score_sentiment(combined)
        scored_news.append(article)

    # ── TAB 1: LIVE FEED ──────────────────────────────
    with tabs[0]:
        if scored_news:
            st.markdown(f'<div style="font-size:10px;color:#64748b;font-family:JetBrains Mono,monospace;margin-top:4px;">Source: {source} — {len(scored_news)} articles</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                min_impact = st.slider("Minimum Impact Score", 0, 10, 0, key="news_min_impact")
            with col2:
                ticker_filter = st.text_input("Filter by Ticker", key="news_ticker_filter", placeholder="e.g., AAPL")

            filtered = scored_news
            if min_impact > 0:
                filtered = [n for n in filtered if n.get("impact_score", 0) >= min_impact]
            if ticker_filter:
                filtered = [n for n in filtered if ticker_filter.upper() in (n.get("ticker", "") or "").upper() or ticker_filter.lower() in n.get("title", "").lower()]

            for article in filtered[:25]:
                impact = article.get("impact_score", 0)
                sentiment = article.get("sentiment_score", 0)
                border_color = Palette.RED if impact >= 7 else Palette.AMBER if impact >= 4 else Palette.BORDER

                ticker_badge = ""
                if article.get("ticker"):
                    ticker_badge = f'<span style="background:{Palette.ACCENT_BLUE}22; color:{Palette.ACCENT_BLUE}; padding:1px 6px; border-radius:3px; font-size:10px; margin-right:6px;">{article["ticker"]}</span>'

                st.markdown(f"""
                <div style="background:{Palette.BG_CARD}; border-left:3px solid {border_color}; border-radius:6px; padding:12px 16px; margin-bottom:6px;">
                    <div style="display:flex; justify-content:space-between;">
                        <div style="flex:1;">
                            <div style="color:{Palette.TEXT_PRIMARY}; font-size:14px; font-weight:500; margin-bottom:4px;">{article.get("title", "")}</div>
                            <div style="color:{Palette.TEXT_MUTED}; font-size:11px;">{ticker_badge}{article.get("source", "")} · {fmt_time_ago(article.get("published"))}</div>
                        </div>
                        <div style="text-align:right; min-width:100px;">
                            <div style="font-size:11px;">{impact_label(impact)}</div>
                            <div style="font-size:11px; margin-top:2px;">{sentiment_label(sentiment)}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            empty_state("No news available. Configure at least one news API.", "📡")

    # ── TAB 2: BY IMPACT ──────────────────────────────
    with tabs[1]:
        if scored_news:
            sorted_by_impact = sorted(scored_news, key=lambda x: x.get("impact_score", 0), reverse=True)
            cols = st.columns(3)
            with cols[0]:
                metric_card("Critical (8+)", str(len([n for n in scored_news if n.get("impact_score", 0) >= 8])))
            with cols[1]:
                metric_card("High (5-7)", str(len([n for n in scored_news if 5 <= n.get("impact_score", 0) <= 7])))
            with cols[2]:
                metric_card("Low (0-4)", str(len([n for n in scored_news if n.get("impact_score", 0) < 5])))

            st.markdown("---")
            for article in sorted_by_impact[:10]:
                impact = article.get("impact_score", 0)
                st.markdown(f"""
                <div style="display:flex; align-items:center; background:{Palette.BG_CARD}; border-radius:6px; padding:10px 14px; margin-bottom:6px;">
                    <div style="min-width:60px; font-size:24px; font-weight:700; color:{Palette.RED if impact >= 7 else Palette.AMBER if impact >= 4 else Palette.TEXT_MUTED}; text-align:center;">{impact}</div>
                    <div style="flex:1; margin-left:12px;">
                        <div style="color:{Palette.TEXT_PRIMARY}; font-size:13px; font-weight:500;">{article.get("title", "")}</div>
                        <div style="color:{Palette.TEXT_MUTED}; font-size:11px; margin-top:2px;">{article.get("source", "")}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 3: SENTIMENT ──────────────────────────────
    with tabs[2]:
        if scored_news:
            import numpy as np
            sentiments = [n.get("sentiment_score", 0) for n in scored_news]
            avg = np.mean(sentiments) if sentiments else 0

            cols = st.columns(3)
            with cols[0]:
                metric_card("Bullish", str(len([s for s in sentiments if s > 0.3])))
            with cols[1]:
                metric_card("Bearish", str(len([s for s in sentiments if s < -0.3])))
            with cols[2]:
                metric_card("Avg Sentiment", f"{avg:+.2f}", source=sentiment_label(avg))

            st.markdown("---")
            sorted_sent = sorted(scored_news, key=lambda x: x.get("sentiment_score", 0))

            col_bear, col_bull = st.columns(2)
            with col_bear:
                st.markdown("**Most Bearish:**")
                for a in sorted_sent[:5]:
                    st.markdown(f'<div style="color:{Palette.RED}; font-size:13px; margin-bottom:4px;">▼ {a.get("title", "")[:80]}</div>', unsafe_allow_html=True)
            with col_bull:
                st.markdown("**Most Bullish:**")
                for a in sorted_sent[-5:]:
                    st.markdown(f'<div style="color:{Palette.GREEN}; font-size:13px; margin-bottom:4px;">▲ {a.get("title", "")[:80]}</div>', unsafe_allow_html=True)

    # ── TAB 4: CATALYST WATCHLIST ─────────────────────
    with tabs[3]:
        st.subheader("Custom Catalyst Watchlist")
        watch_tickers = st.text_input("Tickers to watch", "AAPL, MSFT, NVDA, TSLA", key="catalyst_tickers")
        watch_keywords = st.text_input("Keywords to flag", "earnings, guidance, FDA, acquisition", key="catalyst_keywords")

        tickers_list = [t.strip().upper() for t in watch_tickers.split(",") if t.strip()]
        keywords_list = [k.strip().lower() for k in watch_keywords.split(",") if k.strip()]

        if st.button("Scan Watchlist", key="scan_watchlist"):
            if scored_news:
                matches = []
                for article in scored_news:
                    title_lower = article.get("title", "").lower()
                    text_lower = article.get("text", "").lower()
                    combined = f"{title_lower} {text_lower}"
                    ticker = article.get("ticker", "").upper()

                    ticker_match = ticker in tickers_list or any(t.lower() in combined for t in tickers_list)
                    kw_match = any(kw in combined for kw in keywords_list)

                    if ticker_match or kw_match:
                        matches.append(article)

                if matches:
                    st.success(f"Found {len(matches)} matching articles")
                    for article in matches:
                        st.markdown(f"""
                        <div style="background:{Palette.BG_CARD}; border-left:3px solid {Palette.ACCENT_TEAL}; border-radius:6px; padding:10px 14px; margin-bottom:6px;">
                            <div style="color:{Palette.TEXT_PRIMARY}; font-size:13px;">{article.get("title", "")}</div>
                            <div style="color:{Palette.TEXT_MUTED}; font-size:11px; margin-top:4px;">{article.get("source", "")} · {impact_label(article.get("impact_score", 0))}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No matches found in current news feed.")
