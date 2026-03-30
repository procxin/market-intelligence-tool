"""
Market Intelligence Tool — API Setup & Configuration
=============================================
"""

import streamlit as st
from config import APIKeys, APP_NAME, APP_VERSION
from components.cards import section_header, api_status_indicator
from theme import Palette


def render():
    section_header("API Setup & Configuration", "Configure data providers, check connections, view system health", "⚙️")

    tabs = st.tabs(["API Status", "Setup Guide", "System Info"])

    # ── TAB 1: STATUS ─────────────────────────────────
    with tabs[0]:
        st.subheader("API Connection Status")
        status = APIKeys.status()
        total = len(status)
        connected = sum(1 for v in status.values() if v)

        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"""<div class="nexus-card"><div style="color:{Palette.TEXT_SECONDARY}; font-size:12px;">CONNECTED</div>
                <div style="color:{Palette.GREEN}; font-size:28px; font-weight:700;">{connected}/{total}</div></div>""", unsafe_allow_html=True)
        with cols[1]:
            coverage = int(connected / total * 100) if total > 0 else 0
            color = Palette.GREEN if coverage >= 70 else Palette.AMBER if coverage >= 40 else Palette.RED
            st.markdown(f"""<div class="nexus-card"><div style="color:{Palette.TEXT_SECONDARY}; font-size:12px;">COVERAGE</div>
                <div style="color:{color}; font-size:28px; font-weight:700;">{coverage}%</div></div>""", unsafe_allow_html=True)
        with cols[2]:
            mode = "Full" if connected >= 5 else "Partial" if connected >= 2 else "Demo"
            st.markdown(f"""<div class="nexus-card"><div style="color:{Palette.TEXT_SECONDARY}; font-size:12px;">MODE</div>
                <div style="color:{Palette.TEXT_PRIMARY}; font-size:28px; font-weight:700;">{mode}</div></div>""", unsafe_allow_html=True)

        st.markdown("---")
        for name, is_configured in status.items():
            api_status_indicator(name, is_configured)

        st.markdown("---")
        st.info("💡 yfinance is always available as a fallback and requires no API key.")

    # ── TAB 2: SETUP GUIDE ────────────────────────────
    with tabs[1]:
        st.subheader("API Key Setup Guide")

        guides = [
            ("FRED (Federal Reserve)", "FRED_API_KEY", "Unlimited", "⭐⭐⭐ Critical", "Rates, yields, spreads, Fed balance sheet, M2, CPI", "https://fred.stlouisfed.org/docs/api/api_key.html"),
            ("Financial Modeling Prep", "FMP_API_KEY", "250 req/day", "⭐⭐⭐ High", "Quotes, fundamentals, news, earnings, economic calendar", "https://financialmodelingprep.com/developer/docs/"),
            ("Finnhub", "FINNHUB_API_KEY", "60 req/min", "⭐⭐⭐ High", "Real-time quotes, news, sentiment, earnings", "https://finnhub.io/docs/api"),
            ("CoinGecko", "COINGECKO_API_KEY", "10-30 req/min", "⭐⭐ High", "Crypto prices, market data, trending", "https://www.coingecko.com/en/api/documentation"),
            ("Alpha Vantage", "ALPHA_VANTAGE_API_KEY", "25 req/day", "⭐⭐ Medium", "FX, commodities, technicals", "https://www.alphavantage.co/support/#api-key"),
            ("NewsData.io", "NEWSDATA_API_KEY", "200 req/day", "⭐ Low", "Global news with business filtering", "https://newsdata.io/documentation"),
            ("Polygon.io", "POLYGON_API_KEY", "5 req/min", "⭐ Optional", "Premium tick-level data, options", "https://polygon.io/docs/stocks"),
        ]

        for name, env_var, free_tier, priority, covers, url in guides:
            with st.expander(f"{name} — {priority}"):
                st.markdown(f"**Free Tier:** {free_tier}")
                st.markdown(f"**Covers:** {covers}")
                st.markdown(f"**Docs:** [{url}]({url})")
                st.code(f"# Add to .env:\n{env_var}=your_key_here", language="bash")

        st.markdown("---")
        st.subheader("Quick Start")
        st.code("cp .env.example .env\n# Edit .env with your keys\npip install -r requirements.txt\nstreamlit run app.py", language="bash")

    # ── TAB 3: SYSTEM INFO ────────────────────────────
    with tabs[2]:
        st.subheader("System Information")
        for k, v in {"Application": APP_NAME, "Version": APP_VERSION, "Framework": "Streamlit + Plotly", "Cache": "DuckDB + In-Memory TTL", "Architecture": "Multi-provider with fallback chains"}.items():
            st.markdown(f"**{k}:** {v}")

        st.markdown("---")
        st.subheader("Data Flow")
        st.markdown("""
        1. API request → Rate-limit check → HTTP with retry
        2. Response → Normalize → Memory cache (TTL) + DuckDB
        3. UI reads memory → Falls back to DuckDB → Falls back to live fetch
        4. Every tile displays source + freshness watermark

        **Fallback Chain:** Prices: FMP → yfinance | News: FMP → Finnhub → NewsData | Macro: FRED | Crypto: CoinGecko
        """)
