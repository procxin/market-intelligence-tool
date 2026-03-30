"""
Market Intelligence Tool — Liquidity & Funding Dashboard
=================================================
The "canary" section: rates, spreads, central bank signals.
"""

import streamlit as st
import pandas as pd

from config import FRED_SERIES
from data.cache import cached_fetch, source_watermark
from data.api_clients import fred_series, fred_latest
from components.cards import metric_card, section_header, empty_state
from components.charts import price_chart, area_chart, multi_line_chart, gauge_chart
from theme import Palette
from utils.formatting import fmt_number, fmt_pct


def _load_fred(series_id: str, label: str, limit: int = 252):
    """Load a FRED series with caching."""
    return cached_fetch(
        f"fred_{series_id}",
        lambda: fred_series(series_id, limit=limit).to_dict("records"),
        mem_ttl=300, db_ttl=3600, source=f"FRED ({series_id})"
    )


def render():
    section_header("Liquidity & Funding Dashboard", "Real-time rates, spreads, and central bank balance sheets — the canary signals", "🏦")

    # Check FRED availability
    from config import APIKeys
    if not APIKeys.FRED:
        st.warning("⚠️ FRED API key not configured. Add FRED_API_KEY to your .env file for full liquidity data. Showing available data only.")

    tabs = st.tabs(["Key Rates", "Yield Curve & Spreads", "Central Bank", "Early Warnings"])

    # ────────────────────────────────────────────────────
    # TAB 1: KEY RATES
    # ────────────────────────────────────────────────────
    with tabs[0]:
        rate_series = {
            "Fed Funds": "FEDFUNDS",
            "SOFR": "SOFR",
            "EFFR": "EFFR",
            "2Y Treasury": "DGS2",
            "10Y Treasury": "DGS10",
            "30Y Treasury": "DGS30",
        }

        cols = st.columns(3)
        for i, (label, sid) in enumerate(rate_series.items()):
            with cols[i % 3]:
                val = cached_fetch(
                    f"fred_latest_{sid}",
                    lambda s=sid: fred_latest(s),
                    mem_ttl=300, source="FRED"
                )
                metric_card(label, f"{val:.2f}%" if val is not None else "—", source=source_watermark(f"fred_latest_{sid}"))

        st.markdown("---")

        # Historical charts
        st.subheader("Rate History (1 Year)")
        selected_rates = st.multiselect(
            "Select rates to chart",
            list(rate_series.keys()),
            default=["Fed Funds", "2Y Treasury", "10Y Treasury"],
            key="liq_rates_sel",
        )

        if selected_rates:
            chart_data = {}
            for name in selected_rates:
                sid = rate_series[name]
                records = _load_fred(sid, name)
                if records:
                    df = pd.DataFrame(records)
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.set_index("date")
                    chart_data[name] = df["value"]

            if chart_data:
                combined = pd.DataFrame(chart_data)
                fig = multi_line_chart(combined, list(chart_data.keys()), title="Key Rates (%)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                empty_state("No rate data loaded. Configure FRED API key.", "🔑")

    # ────────────────────────────────────────────────────
    # TAB 2: YIELD CURVE & SPREADS
    # ────────────────────────────────────────────────────
    with tabs[1]:
        spread_series = {
            "2s10s Spread": "T10Y2Y",
            "10Y-3M Spread": "T10Y3M",
            "HY OAS Spread": "BAMLH0A0HYM2",
            "IG OAS Spread": "BAMLC0A4CBBB",
        }

        cols = st.columns(4)
        for i, (label, sid) in enumerate(spread_series.items()):
            with cols[i]:
                val = cached_fetch(
                    f"fred_latest_{sid}",
                    lambda s=sid: fred_latest(s),
                    mem_ttl=300, source="FRED"
                )
                is_inverted = val is not None and val < 0 and sid in ["T10Y2Y", "T10Y3M"]
                delta_val = val if val is not None else None
                metric_card(
                    label + (" ⚠️ INVERTED" if is_inverted else ""),
                    f"{val:.2f}%" if val is not None else "—",
                    source=source_watermark(f"fred_latest_{sid}")
                )

        st.markdown("---")
        st.subheader("Spread History")

        for label, sid in spread_series.items():
            records = _load_fred(sid, label)
            if records:
                df = pd.DataFrame(records)
                df["date"] = pd.to_datetime(df["date"])
                fig = area_chart(df, "date", "value", title=label, height=300)
                if sid in ["T10Y2Y", "T10Y3M"]:
                    fig.add_hline(y=0, line_dash="dash", line_color=Palette.RED, annotation_text="Inversion")
                st.plotly_chart(fig, use_container_width=True)

    # ────────────────────────────────────────────────────
    # TAB 3: CENTRAL BANK
    # ────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("Fed Balance Sheet")
        bs_data = _load_fred("WALCL", "Fed Balance Sheet", limit=520)
        if bs_data:
            df = pd.DataFrame(bs_data)
            df["date"] = pd.to_datetime(df["date"])
            df["value_T"] = df["value"] / 1e6  # WALCL is in millions
            latest = df["value_T"].iloc[-1] if not df.empty else 0
            metric_card("Total Assets", f"${latest:.2f}T", source="FRED (WALCL)")
            fig = area_chart(df, "date", "value_T", title="Fed Total Assets ($T)", color=Palette.ACCENT_INDIGO)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Fed balance sheet data requires FRED API key.", "🔑")

        st.markdown("---")
        st.subheader("M2 Money Supply")
        m2_data = _load_fred("M2SL", "M2", limit=520)
        if m2_data:
            df = pd.DataFrame(m2_data)
            df["date"] = pd.to_datetime(df["date"])
            df["value_T"] = df["value"] / 1e3  # M2SL is in billions
            fig = area_chart(df, "date", "value_T", title="M2 Money Supply ($T)", color=Palette.ACCENT_TEAL)
            st.plotly_chart(fig, use_container_width=True)

    # ────────────────────────────────────────────────────
    # TAB 4: EARLY WARNINGS
    # ────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("Stress Indicators")
        st.markdown("Monitor these for early signs of liquidity stress:")

        warning_indicators = {
            "2s10s Spread": ("T10Y2Y", "Negative = yield curve inversion (recession signal)"),
            "TED Spread": ("TEDRATE", "High = banking stress, interbank lending risk"),
            "Commercial Paper": ("DTBSPCKM", "Spike = short-term funding stress"),
            "HY Credit Spread": ("BAMLH0A0HYM2", "Widening = risk aversion, credit stress"),
        }

        for label, (sid, description) in warning_indicators.items():
            val = cached_fetch(
                f"fred_latest_{sid}",
                lambda s=sid: fred_latest(s),
                mem_ttl=300, source="FRED"
            )
            col1, col2 = st.columns([1, 2])
            with col1:
                metric_card(label, f"{val:.2f}" if val is not None else "—")
            with col2:
                st.markdown(f"*{description}*")
                if val is not None:
                    # Simple traffic light
                    if sid == "T10Y2Y" and val < 0:
                        st.error("⚠️ INVERTED — Historically precedes recessions by 6-18 months")
                    elif sid == "BAMLH0A0HYM2" and val > 5:
                        st.warning("⚠️ Elevated — Credit stress rising")
                    else:
                        st.success("✅ Normal range")
            st.markdown("---")
