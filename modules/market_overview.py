"""
Market Intelligence Tool — Global Market Overview
==========================================
Live indices, commodities, FX, bonds, sector performance.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import MAJOR_INDICES, COMMODITIES, FX_PAIRS, BONDS, VOLATILITY, SECTOR_ETFS
from data.cache import cached_fetch, source_watermark
from data.api_clients import yf_get_quotes, fmp_sector_performance, yf_get_history, get_market_overview
from components.cards import metric_card, section_header, empty_state, data_table_with_colors
from components.charts import bar_chart, price_chart, multi_line_chart
from components.filters import time_range_selector
from theme import Palette
from utils.formatting import fmt_number, fmt_pct, color_for_value


def render():
    section_header("Global Market Overview", "Cross-asset snapshot — equities, bonds, commodities, FX, volatility", "🌍")

    # ── Top-level tabs ───────────────────────────────────
    tabs = st.tabs(["Equities", "Commodities", "FX & Rates", "Volatility", "Sectors"])

    # ────────────────────────────────────────────────────
    # TAB 1: EQUITIES
    # ────────────────────────────────────────────────────
    with tabs[0]:
        with st.spinner("Loading equity indices..."):
            cache_key = "mkt_indices"
            data = cached_fetch(
                cache_key,
                lambda: get_market_overview(MAJOR_INDICES)[0].to_dict("records"),
                mem_ttl=60, source="yfinance"
            )
        if data:
            df = pd.DataFrame(data)
            # Metric cards row
            cols = st.columns(5)
            for i, row in df.head(5).iterrows():
                with cols[i % 5]:
                    metric_card(
                        row["name"],
                        fmt_number(row["price"]),
                        delta=row.get("pct_change", 0),
                        source=source_watermark(cache_key),
                    )

            st.markdown("---")
            # Full table
            st.subheader("All Indices")
            data_table_with_colors(df)

            # Performance chart
            st.subheader("Index Comparison")
            period = time_range_selector(key="eq_time")
            selected = st.multiselect(
                "Select indices to compare",
                options=list(MAJOR_INDICES.keys()),
                default=["S&P 500", "Nasdaq 100", "STOXX 600"],
                key="eq_compare",
            )
            if selected:
                chart_data = {}
                for name in selected:
                    sym = MAJOR_INDICES[name]
                    hist = yf_get_history(sym, period=period)
                    if not hist.empty:
                        chart_data[name] = hist["Close"]
                if chart_data:
                    combined = pd.DataFrame(chart_data)
                    fig = multi_line_chart(combined, list(chart_data.keys()), title="Normalized Performance", normalize=True)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Unable to load equity data. Check API connections.")

    # ────────────────────────────────────────────────────
    # TAB 2: COMMODITIES
    # ────────────────────────────────────────────────────
    with tabs[1]:
        with st.spinner("Loading commodities..."):
            comm_data = cached_fetch(
                "mkt_commodities",
                lambda: yf_get_quotes(COMMODITIES).to_dict("records"),
                mem_ttl=60, source="yfinance"
            )
        if comm_data:
            df = pd.DataFrame(comm_data)
            cols = st.columns(4)
            for i, row in df.head(4).iterrows():
                with cols[i % 4]:
                    metric_card(row["name"], fmt_number(row["price"]), delta=row.get("pct_change", 0))

            st.markdown("---")
            # Bar chart of daily changes
            if not df.empty:
                fig = bar_chart(
                    df["name"].tolist(),
                    df["pct_change"].tolist(),
                    title="Daily Change (%)",
                    horizontal=True,
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("No commodity data available.")

    # ────────────────────────────────────────────────────
    # TAB 3: FX & RATES
    # ────────────────────────────────────────────────────
    with tabs[2]:
        col_fx, col_rates = st.columns(2)
        with col_fx:
            st.subheader("Major FX Pairs")
            with st.spinner("Loading FX..."):
                fx_data = cached_fetch(
                    "mkt_fx",
                    lambda: yf_get_quotes(FX_PAIRS).to_dict("records"),
                    mem_ttl=60, source="yfinance"
                )
            if fx_data:
                data_table_with_colors(pd.DataFrame(fx_data))
            else:
                empty_state("No FX data.")

        with col_rates:
            st.subheader("Treasury Yields")
            with st.spinner("Loading bonds..."):
                bond_data = cached_fetch(
                    "mkt_bonds",
                    lambda: yf_get_quotes(BONDS).to_dict("records"),
                    mem_ttl=60, source="yfinance"
                )
            if bond_data:
                data_table_with_colors(pd.DataFrame(bond_data))
            else:
                empty_state("No bond data.")

    # ────────────────────────────────────────────────────
    # TAB 4: VOLATILITY
    # ────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("Volatility Indices")
        with st.spinner("Loading volatility..."):
            vol_data = cached_fetch(
                "mkt_vol",
                lambda: yf_get_quotes(VOLATILITY).to_dict("records"),
                mem_ttl=60, source="yfinance"
            )
        if vol_data:
            df = pd.DataFrame(vol_data)
            cols = st.columns(len(df))
            for i, row in df.iterrows():
                with cols[i]:
                    metric_card(row["name"], fmt_number(row["price"]), delta=row.get("pct_change", 0))

            # VIX history
            vix_hist = yf_get_history("^VIX", period="1y")
            if not vix_hist.empty:
                fig = price_chart(vix_hist, title="VIX — 1 Year", value_col="Close")
                # Add regime bands
                fig.add_hline(y=20, line_dash="dash", line_color=Palette.AMBER, annotation_text="Normal/Elevated")
                fig.add_hline(y=30, line_dash="dash", line_color=Palette.RED, annotation_text="High Vol")
                st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("No volatility data.")

    # ────────────────────────────────────────────────────
    # TAB 5: SECTORS
    # ────────────────────────────────────────────────────
    with tabs[4]:
        st.subheader("Sector Performance")
        with st.spinner("Loading sectors..."):
            sector_data = cached_fetch(
                "mkt_sectors",
                lambda: yf_get_quotes(SECTOR_ETFS).to_dict("records"),
                mem_ttl=60, source="yfinance"
            )
        if sector_data:
            df = pd.DataFrame(sector_data)
            if not df.empty:
                df_sorted = df.sort_values("pct_change", ascending=True)
                fig = bar_chart(
                    df_sorted["name"].tolist(),
                    df_sorted["pct_change"].tolist(),
                    title="Sector ETFs — Daily Change (%)",
                    horizontal=True,
                    height=500,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")
                data_table_with_colors(df)
        else:
            empty_state("No sector data.")
