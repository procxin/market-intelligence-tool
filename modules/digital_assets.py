"""
Market Intelligence Tool — Digital Assets & On-Chain Intelligence
=========================================================
Crypto prices, funding rates, on-chain proxies, correlation analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np

from config import CRYPTO_IDS
from data.cache import cached_fetch, source_watermark
from data.api_clients import cg_prices, cg_market_chart, cg_global, cg_trending, yf_get_history
from components.cards import section_header, metric_card, empty_state
from components.charts import price_chart, bar_chart, heatmap, multi_line_chart
from theme import Palette
from utils.formatting import fmt_number, fmt_currency, fmt_pct
from utils.indicators import correlation_matrix


def render():
    section_header("Digital Assets & On-Chain Intelligence", "Crypto markets, funding, on-chain signals, cross-asset correlations", "₿")

    tabs = st.tabs(["Market Overview", "Asset Deep Dive", "Correlations", "Trending"])

    # ── TAB 1: MARKET OVERVIEW ─────────────────────────
    with tabs[0]:
        with st.spinner("Loading crypto market data..."):
            global_data = cached_fetch("crypto_global", lambda: cg_global(), mem_ttl=120, source="CoinGecko") or {}

        if global_data:
            cols = st.columns(4)
            with cols[0]:
                total_mcap = global_data.get("total_market_cap", {}).get("usd", 0)
                metric_card("Total Market Cap", fmt_number(total_mcap, prefix="$"), source="CoinGecko")
            with cols[1]:
                total_vol = global_data.get("total_volume", {}).get("usd", 0)
                metric_card("24h Volume", fmt_number(total_vol, prefix="$"))
            with cols[2]:
                btc_dom = global_data.get("market_cap_percentage", {}).get("btc", 0)
                metric_card("BTC Dominance", fmt_pct(btc_dom))
            with cols[3]:
                active = global_data.get("active_cryptocurrencies", 0)
                metric_card("Active Coins", fmt_number(active, decimals=0))

        st.markdown("---")

        with st.spinner("Loading prices..."):
            ids = list(CRYPTO_IDS.values())
            prices = cached_fetch("crypto_prices", lambda: cg_prices(ids), mem_ttl=120, source="CoinGecko") or {}

        if prices:
            rows = []
            for name, coin_id in CRYPTO_IDS.items():
                data = prices.get(coin_id, {})
                if data:
                    rows.append({
                        "Asset": name, "Price": data.get("usd", 0),
                        "24h %": round(data.get("usd_24h_change", 0), 2),
                        "Market Cap": data.get("usd_market_cap", 0),
                    })

            if rows:
                df = pd.DataFrame(rows)
                top_cols = st.columns(5)
                for i, row in df.head(5).iterrows():
                    with top_cols[i]:
                        metric_card(row["Asset"], fmt_currency(row["Price"]), delta=row["24h %"])

                st.markdown("---")
                df_sorted = df.sort_values("24h %", ascending=True)
                fig = bar_chart(df_sorted["Asset"].tolist(), df_sorted["24h %"].tolist(), title="24h Performance (%)", horizontal=True, height=450)
                st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Could not load crypto prices.", "⏳")

    # ── TAB 2: ASSET DEEP DIVE ────────────────────────
    with tabs[1]:
        selected_coin = st.selectbox("Select Asset", list(CRYPTO_IDS.keys()), key="crypto_select")
        coin_id = CRYPTO_IDS[selected_coin]
        days = st.radio("Period", ["7d", "30d", "90d", "365d"], horizontal=True, key="crypto_period")
        days_int = int(days.replace("d", ""))

        with st.spinner(f"Loading {selected_coin} chart..."):
            chart_data = cached_fetch(
                f"crypto_chart_{coin_id}_{days_int}",
                lambda: cg_market_chart(coin_id, days=days_int).to_dict("records"),
                mem_ttl=300, source="CoinGecko"
            )

        if chart_data:
            df = pd.DataFrame(chart_data)
            df["date"] = pd.to_datetime(df["date"])
            fig = price_chart(df, title=f"{selected_coin} — {days}", date_col="date", value_col="price", height=450)
            st.plotly_chart(fig, use_container_width=True)

            if len(df) > 1:
                current, start = df["price"].iloc[-1], df["price"].iloc[0]
                pct_change = ((current - start) / start * 100) if start else 0
                cols = st.columns(4)
                with cols[0]:
                    metric_card("Current", fmt_currency(current))
                with cols[1]:
                    metric_card(f"{days} High", fmt_currency(df["price"].max()))
                with cols[2]:
                    metric_card(f"{days} Low", fmt_currency(df["price"].min()))
                with cols[3]:
                    metric_card(f"{days} Return", fmt_pct(pct_change))

    # ── TAB 3: CORRELATIONS ───────────────────────────
    with tabs[2]:
        st.subheader("Cross-Asset Correlation Matrix")
        corr_assets = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD", "S&P 500": "^GSPC", "Gold": "GC=F", "DXY": "DX-Y.NYB"}

        with st.spinner("Computing correlations..."):
            price_data = {}
            for name, sym in corr_assets.items():
                hist = yf_get_history(sym, period="6mo")
                if not hist.empty and "Close" in hist.columns:
                    price_data[name] = hist["Close"]

            if len(price_data) >= 3:
                combined = pd.DataFrame(price_data).dropna()
                corr = correlation_matrix(combined)
                fig = heatmap(corr, title="90-Day Return Correlations", height=500)
                st.plotly_chart(fig, use_container_width=True)

    # ── TAB 4: TRENDING ───────────────────────────────
    with tabs[3]:
        st.subheader("Trending Coins")
        trending = cached_fetch("crypto_trending", lambda: cg_trending(), mem_ttl=300, source="CoinGecko") or []
        if trending:
            for coin in trending[:10]:
                name = coin.get("name", "")
                symbol = coin.get("symbol", "")
                rank = coin.get("market_cap_rank", "—")
                st.markdown(f"""
                <div style="display:flex; align-items:center; background:{Palette.BG_CARD}; border-radius:6px; padding:10px 14px; margin-bottom:6px;">
                    <div style="min-width:40px; text-align:center; color:{Palette.TEXT_MUTED};">#{rank}</div>
                    <div style="flex:1; margin-left:12px;">
                        <span style="color:{Palette.TEXT_PRIMARY}; font-weight:600;">{name}</span>
                        <span style="color:{Palette.TEXT_MUTED}; font-size:12px; margin-left:6px;">{symbol}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            empty_state("No trending data available.")
