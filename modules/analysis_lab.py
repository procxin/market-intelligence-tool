"""
Market Intelligence Tool — Interactive Analysis Lab
============================================
Custom chart builder, correlation matrix, scenario stress tester, exports.
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from datetime import datetime

from data.api_clients import yf_get_history
from components.cards import section_header, metric_card, empty_state
from components.charts import multi_line_chart, heatmap
from components.filters import multi_ticker_input, time_range_selector
from theme import Palette
from utils.indicators import correlation_matrix, drawdown
from utils.formatting import fmt_pct, fmt_currency


def render():
    section_header("Interactive Analysis Lab", "Custom charts, correlations, regime detection, scenario stress testing", "🔬")

    tabs = st.tabs(["Chart Builder", "Correlation Matrix", "Stress Tester", "Export"])

    # ── TAB 1: CHART BUILDER ──────────────────────────
    with tabs[0]:
        st.subheader("Multi-Asset Chart Builder")
        tickers = multi_ticker_input(key="lab_tickers", label="Tickers (comma-separated)")
        if not tickers:
            tickers = ["SPY", "QQQ", "GLD", "TLT"]
            st.caption("Default: SPY, QQQ, GLD, TLT")

        period = time_range_selector(key="lab_period")
        normalize = st.checkbox("Normalize to % change", value=True, key="lab_normalize")

        if tickers:
            with st.spinner("Loading chart data..."):
                price_data = {}
                for ticker in tickers:
                    hist = yf_get_history(ticker, period=period)
                    if not hist.empty and "Close" in hist.columns:
                        price_data[ticker] = hist["Close"]

            if price_data:
                combined = pd.DataFrame(price_data).dropna()
                if not combined.empty:
                    fig = multi_line_chart(combined, list(price_data.keys()), title="Multi-Asset Performance", normalize=normalize, height=500)
                    st.plotly_chart(fig, use_container_width=True)

                    # Stats table
                    st.subheader("Performance Statistics")
                    stats = []
                    for ticker in price_data:
                        if ticker not in combined.columns:
                            continue
                        series = combined[ticker]
                        if len(series) < 2:
                            continue
                        returns = series.pct_change().dropna()
                        total_return = (series.iloc[-1] / series.iloc[0] - 1) * 100
                        ann_vol = returns.std() * np.sqrt(252) * 100
                        max_dd = drawdown(series).min() * 100
                        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
                        stats.append({
                            "Ticker": ticker, "Total Return": f"{total_return:+.2f}%",
                            "Ann. Vol": f"{ann_vol:.1f}%", "Max DD": f"{max_dd:.1f}%",
                            "Sharpe": f"{sharpe:.2f}", "Price": fmt_currency(series.iloc[-1]),
                        })
                    if stats:
                        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

                    with st.expander("Drawdown Analysis"):
                        fig_dd = go.Figure()
                        for i, ticker in enumerate(price_data):
                            if ticker in combined.columns:
                                dd = drawdown(combined[ticker]) * 100
                                fig_dd.add_trace(go.Scatter(x=combined.index, y=dd, mode="lines", fill="tozeroy", line=dict(color=Palette.SERIES[i % len(Palette.SERIES)], width=1.5), name=ticker))
                        fig_dd.update_layout(title="Drawdown (%)", height=350, yaxis_title="%")
                        st.plotly_chart(fig_dd, use_container_width=True)

    # ── TAB 2: CORRELATION MATRIX ─────────────────────
    with tabs[1]:
        st.subheader("Correlation Matrix")
        corr_tickers = multi_ticker_input(key="corr_tickers", label="Tickers for correlation")
        if not corr_tickers:
            corr_tickers = ["SPY", "QQQ", "IWM", "GLD", "TLT", "BTC-USD", "CL=F"]
            st.caption("Default: SPY, QQQ, IWM, GLD, TLT, BTC-USD, CL=F")

        corr_period = st.selectbox("Lookback", ["3mo", "6mo", "1y", "2y"], index=1, key="corr_period")

        if st.button("Compute Correlations", key="compute_corr"):
            with st.spinner("Computing..."):
                price_data = {}
                for ticker in corr_tickers:
                    hist = yf_get_history(ticker, period=corr_period)
                    if not hist.empty and "Close" in hist.columns:
                        price_data[ticker] = hist["Close"]

                if len(price_data) >= 2:
                    combined = pd.DataFrame(price_data).dropna()
                    corr = correlation_matrix(combined)
                    fig = heatmap(corr, title=f"Return Correlations ({corr_period})", height=600)
                    st.plotly_chart(fig, use_container_width=True)

                    pairs = []
                    cols_list = corr.columns.tolist()
                    for i in range(len(cols_list)):
                        for j in range(i + 1, len(cols_list)):
                            val = corr.iloc[i, j]
                            if abs(val) > 0.6:
                                pairs.append({"Pair": f"{cols_list[i]} / {cols_list[j]}", "Correlation": f"{val:.3f}"})
                    if pairs:
                        st.subheader("Notable Correlations (|r| > 0.6)")
                        st.dataframe(pd.DataFrame(pairs), use_container_width=True, hide_index=True)

    # ── TAB 3: STRESS TESTER ─────────────────────────
    with tabs[2]:
        st.subheader("Scenario Stress Tester")
        st.markdown("**Portfolio:**")
        stress_tickers = st.text_input("Tickers", "SPY, QQQ, GLD, TLT", key="stress_tickers")
        stress_weights = st.text_input("Weights (sum to 1.0)", "0.4, 0.3, 0.15, 0.15", key="stress_weights")

        tickers_list = [t.strip().upper() for t in stress_tickers.split(",") if t.strip()]
        try:
            weights_list = [float(w.strip()) for w in stress_weights.split(",") if w.strip()]
        except ValueError:
            weights_list = [1.0 / max(len(tickers_list), 1)] * len(tickers_list)

        scenarios = {
            "Oil +20%": {"CL=F": 0.20},
            "10Y Yield +50bp": {"TLT": -0.08, "SPY": -0.03},
            "VIX to 40": {"SPY": -0.05, "QQQ": -0.07, "GLD": 0.02},
            "Recession": {"SPY": -0.20, "QQQ": -0.25, "GLD": 0.10, "TLT": 0.12},
            "Inflation Surge": {"GLD": 0.15, "TLT": -0.10, "SPY": -0.08},
            "USD +5%": {"GLD": -0.03, "SPY": -0.02},
        }

        selected_scenario = st.selectbox("Select Scenario", list(scenarios.keys()), key="stress_scenario")

        if st.button("Run Stress Test", key="run_stress"):
            shock = scenarios[selected_scenario]
            results = []
            total_impact = 0
            for ticker, weight in zip(tickers_list, weights_list):
                shock_pct = shock.get(ticker, shock.get("SPY", 0) * 0.5 if "SPY" in shock else 0)
                weighted_impact = shock_pct * weight * 100
                total_impact += weighted_impact
                results.append({"Ticker": ticker, "Weight": f"{weight:.1%}", "Shock": f"{shock_pct:+.1%}", "Impact": f"{weighted_impact:+.2f}%"})

            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
            color = Palette.GREEN if total_impact > 0 else Palette.RED
            st.markdown(f"""
            <div style="background:{Palette.BG_CARD}; border:2px solid {color}; border-radius:10px; padding:20px; text-align:center; margin-top:16px;">
                <div style="color:{Palette.TEXT_SECONDARY}; font-size:14px;">Estimated Portfolio Impact</div>
                <div style="color:{color}; font-size:36px; font-weight:700;">{total_impact:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 4: EXPORT ────────────────────────────────
    with tabs[3]:
        st.subheader("Export Data")
        export_tickers = multi_ticker_input(key="export_tickers", label="Tickers to export")
        export_period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3, key="export_period")

        if st.button("Generate Export", key="gen_export") and export_tickers:
            with st.spinner("Preparing..."):
                all_data = {}
                for ticker in export_tickers:
                    hist = yf_get_history(ticker, period=export_period)
                    if not hist.empty:
                        for col in ["Open", "High", "Low", "Close", "Volume"]:
                            if col in hist.columns:
                                all_data[f"{ticker}_{col}"] = hist[col]

                if all_data:
                    export_df = pd.DataFrame(all_data)
                    csv_buffer = io.StringIO()
                    export_df.to_csv(csv_buffer)
                    st.download_button("📥 Download CSV", csv_buffer.getvalue(),
                        file_name=f"nexus_export_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
                    st.success(f"Export ready: {len(export_df)} rows, {len(export_df.columns)} columns")
