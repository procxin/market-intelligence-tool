"""
Market Intelligence Tool — Catalyst & Event Calendar
=============================================
Earnings, FOMC, CPI, GDP, central bank speeches.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from data.cache import cached_fetch, source_watermark
from data.api_clients import fmp_earnings_calendar, fmp_economic_calendar, finnhub_earnings_calendar
from components.cards import section_header, empty_state
from components.charts import bar_chart
from utils.scoring import impact_label


KNOWN_EVENTS = [
    {"type": "FOMC", "description": "Federal Reserve Rate Decision", "impact": 9, "freq": "8x/year"},
    {"type": "CPI", "description": "Consumer Price Index (US)", "impact": 8, "freq": "Monthly"},
    {"type": "NFP", "description": "Non-Farm Payrolls (US)", "impact": 8, "freq": "Monthly"},
    {"type": "GDP", "description": "GDP Advance Estimate (US)", "impact": 7, "freq": "Quarterly"},
    {"type": "ECB", "description": "ECB Rate Decision", "impact": 8, "freq": "6-8x/year"},
    {"type": "PCE", "description": "Core PCE Deflator (US)", "impact": 7, "freq": "Monthly"},
    {"type": "ISM", "description": "ISM Manufacturing PMI", "impact": 6, "freq": "Monthly"},
    {"type": "OPEC", "description": "OPEC+ Meeting", "impact": 7, "freq": "~Monthly"},
]


def _get_earnings(from_d, to_d):
    data = fmp_earnings_calendar(from_d, to_d)
    if data:
        return data
    return finnhub_earnings_calendar(from_d, to_d) or []


def render():
    section_header("Catalyst & Event Calendar", "Upcoming earnings, macro releases, central bank decisions", "📅")
    tabs = st.tabs(["Earnings", "Economic Calendar", "Key Events"])

    from_d = datetime.now().strftime("%Y-%m-%d")
    to_d = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    with tabs[0]:
        with st.spinner("Loading earnings..."):
            earnings = cached_fetch("cal_earnings", lambda: _get_earnings(from_d, to_d), mem_ttl=600, source="FMP/Finnhub")
        if earnings:
            df = pd.DataFrame(earnings)
            cols = [c for c in ["date", "symbol", "epsEstimated", "revenueEstimated"] if c in df.columns] or list(df.columns[:5])
            search = st.text_input("Search ticker", key="earn_search", placeholder="e.g., AAPL")
            if search and "symbol" in df.columns:
                df = df[df["symbol"].str.contains(search.upper(), na=False)]
            st.dataframe(df[cols].head(50), use_container_width=True, hide_index=True)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                daily = df.groupby(df["date"].dt.date).size().reset_index(name="count")
                if not daily.empty:
                    fig = bar_chart([d.strftime("%m/%d") for d in daily["date"]], daily["count"].tolist(), title="Earnings Density", color_by_value=False)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Configure FMP or Finnhub API key for earnings data.", "🔑")

    with tabs[1]:
        with st.spinner("Loading economic calendar..."):
            econ = cached_fetch("cal_economic", lambda: fmp_economic_calendar(from_d, to_d), mem_ttl=600, source="FMP")
        if econ:
            df = pd.DataFrame(econ)
            cols = [c for c in ["date", "event", "country", "actual", "estimate", "previous", "impact"] if c in df.columns] or list(df.columns[:6])
            st.dataframe(df[cols].head(50), use_container_width=True, hide_index=True)
        else:
            empty_state("Economic calendar requires FMP API key.", "🔑")

    with tabs[2]:
        st.subheader("Key Recurring Market Events")
        for ev in KNOWN_EVENTS:
            c1, c2, c3 = st.columns([2, 4, 1])
            with c1:
                st.markdown(f"**{ev['type']}**")
                st.caption(ev["freq"])
            with c2:
                st.markdown(ev["description"])
            with c3:
                st.markdown(impact_label(ev["impact"]))
            st.markdown("---")
