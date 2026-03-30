"""
Market Intelligence Tool — Company & Sector Deep Dive
==============================================
Ticker search → fundamentals, peer comparison, news, charts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from data.cache import cached_fetch, source_watermark
from data.api_clients import (
    yf_get_info, yf_get_history, fmp_company_profile,
    fmp_financials, finnhub_company_news, fmp_news
)
from data.watchlist import add_to_watchlist, is_in_watchlist, remove_from_watchlist
from components.cards import section_header, metric_card, empty_state
from components.charts import candlestick_chart, price_chart, bar_chart
from components.filters import ticker_search, time_range_selector
from theme import Palette
from utils.formatting import fmt_number, fmt_currency, fmt_pct
from utils.indicators import rsi, macd, bollinger_bands, sma
from utils.scoring import score_sentiment, sentiment_label


def render():
    section_header("Company & Sector Deep Dive", "Fundamental analysis, technicals, news sentiment, peer comparison", "🏢")

    ticker = ticker_search(key="company_ticker", label="🔍 Enter Ticker Symbol")

    if not ticker:
        st.markdown(f"""
        <div style="text-align:center; padding:60px 20px; color:{Palette.TEXT_MUTED};">
            <div style="font-size:48px; margin-bottom:16px;">🔍</div>
            <div style="font-size:16px;">Enter a ticker symbol above to begin analysis</div>
            <div style="font-size:13px; margin-top:8px;">Examples: AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Watchlist toggle
    col_title, col_wl = st.columns([3, 1])
    with col_title:
        st.subheader(f"Analysis: {ticker}")
    with col_wl:
        if is_in_watchlist(ticker):
            if st.button("★ Remove from Watchlist", key="wl_remove"):
                remove_from_watchlist(ticker)
                st.rerun()
        else:
            if st.button("☆ Add to Watchlist", key="wl_add"):
                add_to_watchlist(ticker, ticker, "equity")
                st.rerun()

    tabs = st.tabs(["Overview", "Financials", "Technicals", "News & Sentiment"])

    # ── Load core data ──────────────────────────────────
    with st.spinner(f"Loading data for {ticker}..."):
        info = cached_fetch(
            f"company_info_{ticker}",
            lambda: yf_get_info(ticker),
            mem_ttl=300, source="yfinance"
        ) or {}

        fmp_profile = cached_fetch(
            f"fmp_profile_{ticker}",
            lambda: fmp_company_profile(ticker),
            mem_ttl=300, source="FMP"
        ) or {}

    # ── TAB 1: OVERVIEW ────────────────────────────────
    with tabs[0]:
        if info or fmp_profile:
            name = info.get("longName") or fmp_profile.get("companyName", ticker)
            sector = info.get("sector") or fmp_profile.get("sector", "—")
            industry = info.get("industry") or fmp_profile.get("industry", "—")
            mkt_cap = info.get("marketCap") or fmp_profile.get("mktCap")
            price = info.get("currentPrice") or fmp_profile.get("price")
            pe = info.get("trailingPE") or fmp_profile.get("pe")
            fwd_pe = info.get("forwardPE")
            div_yield = info.get("dividendYield")
            beta = info.get("beta") or fmp_profile.get("beta")
            high_52 = info.get("fiftyTwoWeekHigh")
            low_52 = info.get("fiftyTwoWeekLow")

            st.markdown(f"""
            <div class="nexus-header">
                <div style="font-size:24px; font-weight:700; color:{Palette.TEXT_PRIMARY};">{name}</div>
                <div style="color:{Palette.TEXT_SECONDARY}; font-size:13px; margin-top:4px;">{sector} · {industry} · {ticker}</div>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(5)
            with cols[0]:
                metric_card("Price", fmt_currency(price), source=source_watermark(f"company_info_{ticker}"))
            with cols[1]:
                metric_card("Market Cap", fmt_number(mkt_cap, prefix="$"))
            with cols[2]:
                metric_card("P/E (TTM)", fmt_number(pe) if pe else "—")
            with cols[3]:
                metric_card("Forward P/E", fmt_number(fwd_pe) if fwd_pe else "—")
            with cols[4]:
                metric_card("Beta", fmt_number(beta) if beta else "—")

            cols2 = st.columns(4)
            with cols2[0]:
                metric_card("52W High", fmt_currency(high_52) if high_52 else "—")
            with cols2[1]:
                metric_card("52W Low", fmt_currency(low_52) if low_52 else "—")
            with cols2[2]:
                metric_card("Div Yield", fmt_pct(div_yield * 100) if div_yield else "—")
            with cols2[3]:
                metric_card("Sector", sector)

            st.markdown("---")
            period = time_range_selector(key="company_period")
            hist = yf_get_history(ticker, period=period)
            if not hist.empty:
                fig = candlestick_chart(hist, title=f"{ticker} — {period.upper()}")
                st.plotly_chart(fig, use_container_width=True)

            desc = info.get("longBusinessSummary") or fmp_profile.get("description", "")
            if desc:
                with st.expander("Company Description"):
                    st.write(desc[:800])
        else:
            empty_state(f"Could not find data for {ticker}. Check the symbol.")

    # ── TAB 2: FINANCIALS ──────────────────────────────
    with tabs[1]:
        fin_period = st.radio("Period", ["Annual", "Quarterly"], horizontal=True, key="fin_period")
        period_param = "annual" if fin_period == "Annual" else "quarter"

        with st.spinner("Loading financials..."):
            income = cached_fetch(
                f"fin_income_{ticker}_{period_param}",
                lambda: fmp_financials(ticker, "income-statement", period_param),
                mem_ttl=900, source="FMP"
            )

        if income:
            st.subheader("Income Statement")
            df = pd.DataFrame(income)
            key_cols = [c for c in ["date", "revenue", "grossProfit", "operatingIncome", "netIncome", "eps"] if c in df.columns]
            if key_cols:
                st.dataframe(df[key_cols].head(8), use_container_width=True, hide_index=True)

                if "revenue" in df.columns:
                    chart_df = df[["date", "revenue"]].head(8).iloc[::-1]
                    fig = bar_chart(
                        chart_df["date"].tolist(),
                        [r / 1e9 for r in chart_df["revenue"].tolist()],
                        title="Revenue ($B)", color_by_value=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Financial data requires FMP API key.", "🔑")

    # ── TAB 3: TECHNICALS ──────────────────────────────
    with tabs[2]:
        hist = yf_get_history(ticker, period="1y")
        if not hist.empty and "Close" in hist.columns:
            close = hist["Close"]
            rsi_vals = rsi(close)
            current_rsi = rsi_vals.iloc[-1] if not rsi_vals.empty else None
            bb_upper, bb_mid, bb_lower = bollinger_bands(close)
            sma_50 = sma(close, 50)
            sma_200 = sma(close, 200)

            cols = st.columns(4)
            with cols[0]:
                metric_card("RSI (14)", f"{current_rsi:.1f}" if current_rsi else "—")
            with cols[1]:
                macd_l, _, _ = macd(close)
                macd_val = macd_l.iloc[-1] if not macd_l.empty else None
                metric_card("MACD", f"{macd_val:.2f}" if macd_val else "—")
            with cols[2]:
                metric_card("SMA 50", fmt_currency(sma_50.iloc[-1]) if not sma_50.empty else "—")
            with cols[3]:
                metric_card("SMA 200", fmt_currency(sma_200.iloc[-1]) if not sma_200.empty else "—")

            st.markdown("---")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=bb_upper, mode="lines", line=dict(color=Palette.TEXT_MUTED, width=1, dash="dash"), name="Upper BB"))
            fig.add_trace(go.Scatter(x=hist.index, y=bb_lower, mode="lines", line=dict(color=Palette.TEXT_MUTED, width=1, dash="dash"), fill="tonexty", fillcolor="rgba(59,130,246,0.05)", name="Lower BB"))
            fig.add_trace(go.Scatter(x=hist.index, y=close, mode="lines", line=dict(color=Palette.ACCENT_BLUE, width=2), name="Close"))
            fig.add_trace(go.Scatter(x=hist.index, y=sma_50, mode="lines", line=dict(color=Palette.AMBER, width=1), name="SMA 50"))
            fig.add_trace(go.Scatter(x=hist.index, y=sma_200, mode="lines", line=dict(color=Palette.RED, width=1), name="SMA 200"))
            fig.update_layout(title=f"{ticker} — Bollinger Bands & SMAs", height=450)
            st.plotly_chart(fig, use_container_width=True)

            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=hist.index, y=rsi_vals, mode="lines", line=dict(color=Palette.ACCENT_TEAL, width=2)))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color=Palette.RED, annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color=Palette.GREEN, annotation_text="Oversold")
            fig_rsi.update_layout(title="RSI (14)", height=250, yaxis_range=[0, 100])
            st.plotly_chart(fig_rsi, use_container_width=True)
        else:
            empty_state(f"No historical data for {ticker}.")

    # ── TAB 4: NEWS & SENTIMENT ────────────────────────
    with tabs[3]:
        st.subheader(f"Recent News for {ticker}")
        with st.spinner("Loading news..."):
            company_news = cached_fetch(
                f"news_{ticker}",
                lambda: finnhub_company_news(ticker),
                mem_ttl=300, source="Finnhub"
            )
            if not company_news:
                company_news = cached_fetch(
                    f"fmp_news_{ticker}",
                    lambda: fmp_news(tickers=ticker, limit=20),
                    mem_ttl=300, source="FMP"
                )

        if company_news:
            sentiments = []
            for article in company_news[:15]:
                title = article.get("headline") or article.get("title", "")
                source_name = article.get("source") or article.get("site", "")
                summary = article.get("summary") or article.get("text", "")
                combined = f"{title} {summary}"
                sent = score_sentiment(combined)
                sentiments.append(sent)

                st.markdown(f"""
                <div style="background:{Palette.BG_CARD}; border-radius:6px; padding:10px 14px; margin-bottom:6px;">
                    <div style="color:{Palette.TEXT_PRIMARY}; font-size:13px; font-weight:500;">{title}</div>
                    <div style="color:{Palette.TEXT_MUTED}; font-size:11px; margin-top:4px;">{source_name} · {sentiment_label(sent)}</div>
                </div>
                """, unsafe_allow_html=True)

            if sentiments:
                avg_sent = np.mean(sentiments)
                st.markdown("---")
                st.markdown(f"**Aggregate Sentiment:** {sentiment_label(avg_sent)} ({avg_sent:+.2f})")
        else:
            empty_state(f"No news found for {ticker}.", "📰")
