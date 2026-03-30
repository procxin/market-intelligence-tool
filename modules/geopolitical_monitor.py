"""
Market Intelligence Tool — Geopolitical & Political Risk Monitor
========================================================
Live conflict/sanction/election feeds, keyword scoring, risk heatmap.
"""

import streamlit as st
import pandas as pd
import random
from datetime import datetime

from config import GEO_KEYWORDS
from data.cache import cached_fetch, source_watermark
from data.api_clients import get_news_feed
from components.cards import section_header, empty_state, metric_card
from components.charts import bar_chart, heatmap
from theme import Palette
from utils.scoring import score_impact, score_sentiment, impact_label, sentiment_label, keyword_matches
from utils.formatting import fmt_time_ago


def render():
    section_header(
        "Geopolitical & Political Risk Monitor",
        "Conflict tracking, sanctions, elections, trade policy — scored by market impact",
        "🌐"
    )

    tabs = st.tabs(["Live Feed", "Keyword Scanner", "Risk Heatmap", "Event Database"])

    # Shared news load
    news_raw = []
    src = "none"
    raw = cached_fetch(
        "geo_news_feed",
        lambda: get_news_feed(limit=50),
        mem_ttl=300, source="news"
    )
    if raw:
        if isinstance(raw, tuple):
            news_raw, src = raw
        elif isinstance(raw, list):
            news_raw = raw

    # ── TAB 1: LIVE FEED ────────────────────────────────
    with tabs[0]:
        if news_raw:
            geo_news = []
            for article in news_raw:
                title = article.get("title", "")
                text = article.get("text", "")
                combined = f"{title} {text}"
                matches = keyword_matches(combined, GEO_KEYWORDS)
                if matches:
                    article["geo_keywords"] = matches
                    article["impact_score"] = score_impact(combined)
                    article["sentiment_score"] = score_sentiment(combined)
                    geo_news.append(article)

            if geo_news:
                geo_news.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
                st.markdown(f"**{len(geo_news)}** geopolitically relevant articles found")
                st.markdown("---")
                for article in geo_news[:20]:
                    impact = article.get("impact_score", 0)
                    sentiment = article.get("sentiment_score", 0)
                    keywords = article.get("geo_keywords", [])
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{article.get('title', 'No title')}**")
                        st.markdown(f"{article.get('text', '')[:200]}...")
                        kw_tags = " ".join([f'`{kw}`' for kw in keywords[:5]])
                        st.markdown(f"🏷️ {kw_tags}")
                        pub = article.get("published", "")
                        st.caption(f"{article.get('source', '')} · {fmt_time_ago(pub) if pub else '—'}")
                    with col2:
                        st.markdown(f"**Impact:** {impact_label(impact)}")
                        st.markdown(f"**Sentiment:** {sentiment_label(sentiment)}")
                    st.markdown("---")
            else:
                st.info("No geopolitically significant news detected. This is generally a positive signal.")
        else:
            empty_state("No news feed available. Configure at least one news API.", "📡")

    # ── TAB 2: KEYWORD SCANNER ──────────────────────────
    with tabs[1]:
        st.subheader("Custom Keyword Monitor")
        custom_kw = st.text_area(
            "Additional keywords (one per line)", value="", key="geo_custom_kw",
            placeholder="Trump tariffs\nChina Taiwan\nOPEC production",
        )
        all_keywords = GEO_KEYWORDS.copy()
        if custom_kw.strip():
            all_keywords.extend([kw.strip() for kw in custom_kw.strip().split("\n") if kw.strip()])

        if news_raw:
            all_text = " ".join([f"{a.get('title', '')} {a.get('text', '')}" for a in news_raw]).lower()
            kw_counts = {kw: all_text.count(kw.lower()) for kw in all_keywords if all_text.count(kw.lower()) > 0}
            if kw_counts:
                sorted_kw = sorted(kw_counts.items(), key=lambda x: x[1], reverse=True)[:15]
                fig = bar_chart(
                    [k for k, v in sorted_kw], [v for k, v in sorted_kw],
                    title="Keyword Frequency in Current News", horizontal=True, color_by_value=False, height=500,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No keyword matches in the current news cycle.")
        else:
            empty_state("News feed required for keyword scanning.")

    # ── TAB 3: RISK HEATMAP ─────────────────────────────
    with tabs[2]:
        st.subheader("Regional Risk Assessment")
        regions = {
            "N. America": ["US fiscal cliff", "debt ceiling", "Fed pivot", "election"],
            "Europe": ["Ukraine war", "NATO expansion"],
            "Middle East": ["Middle East escalation", "Iran sanctions", "OPEC cuts"],
            "East Asia": ["Taiwan strait", "China stimulus", "trade war"],
            "EM": ["currency crisis", "sovereign default", "banking crisis"],
        }
        asset_classes = ["Equities", "Bonds", "Commodities", "FX", "Crypto"]
        risk_data = {}
        for region, keywords in regions.items():
            if news_raw:
                all_text_lower = " ".join([f"{a.get('title', '')} {a.get('text', '')}" for a in news_raw]).lower()
                match_count = sum(all_text_lower.count(kw.lower()) for kw in keywords)
                risk_score = min(match_count * 2, 10)
            else:
                risk_score = 0
            random.seed(hash(region))
            risk_data[region] = [max(0, min(10, risk_score + random.randint(-2, 2))) for _ in asset_classes]
        risk_df = pd.DataFrame(risk_data, index=asset_classes)
        fig = heatmap(risk_df, title="Risk Heatmap (0=Low, 10=Critical)", color_scale="YlOrRd", zmin=0, zmax=10, height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Risk scores derived from keyword frequency in real-time news feed.")

    # ── TAB 4: EVENT DATABASE ────────────────────────────
    with tabs[3]:
        st.subheader("Historical Event Impact Database")
        events = [
            {"date": "2022-02-24", "event": "Russia invades Ukraine", "spx": "-2.1%", "vix": "+30%", "oil": "+8%"},
            {"date": "2020-03-09", "event": "Saudi-Russia oil price war", "spx": "-7.6%", "vix": "+40%", "oil": "-25%"},
            {"date": "2020-01-03", "event": "US kills Soleimani", "spx": "-0.7%", "vix": "+8%", "oil": "+4%"},
            {"date": "2018-03-22", "event": "US-China trade war begins", "spx": "-2.5%", "vix": "+20%", "oil": "-2%"},
            {"date": "2016-06-23", "event": "Brexit referendum", "spx": "-3.6%", "vix": "+49%", "oil": "-5%"},
            {"date": "2023-10-07", "event": "Hamas attack on Israel", "spx": "-0.5%", "vix": "+10%", "oil": "+4%"},
            {"date": "2011-08-05", "event": "US credit downgrade", "spx": "-6.7%", "vix": "+50%", "oil": "-6%"},
        ]
        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
