"""
Market Intelligence Tool — Institutional-Grade Analytics
====================================================
Entry point: streamlit run app.py
"""

import streamlit as st
import logging
import importlib
import os
from datetime import datetime

# ── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("nexus.log", mode="a"),
    ],
)
logger = logging.getLogger("nexus")

# ── Page config (MUST be first Streamlit call) ──────────────
st.set_page_config(
    page_title="Market Intelligence Tool",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme ───────────────────────────────────────────────────
from theme import inject_css, register_theme, Palette
inject_css()
register_theme()

# ── Access Gate ─────────────────────────────────────────────
def _check_access():
    """Simple password gate to protect API rate limits."""
    try:
        correct_pw = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        correct_pw = os.environ.get("APP_PASSWORD", "")

    if not correct_pw:
        return True  # No password set = open access (local dev)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown(f"""
    <div style="text-align:center; padding:80px 20px;">
        <div style="font-size:32px; font-weight:700; color:{Palette.TEXT_PRIMARY};">◆ Market Intelligence Tool</div>
        <div style="color:{Palette.TEXT_MUTED}; font-size:13px; margin-top:8px; letter-spacing:2px;">INSTITUTIONAL-GRADE ANALYTICS</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pw = st.text_input("Access Code", type="password", placeholder="Enter access code")
        if st.button("Enter", use_container_width=True):
            if pw == correct_pw:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code")
    return False


if not _check_access():
    st.stop()

# ── Page Registry ───────────────────────────────────────────
PAGE_MODULES = {
    "🌍 Market Overview": "modules.market_overview",
    "🏦 Liquidity & Funding": "modules.liquidity_dashboard",
    "🌐 Geopolitical Risk": "modules.geopolitical_monitor",
    "📅 Catalyst Calendar": "modules.catalyst_calendar",
    "🏢 Company Deep Dive": "modules.company_deep_dive",
    "₿ Digital Assets": "modules.digital_assets",
    "📰 News & Sentiment": "modules.news_sentiment",
    "🔬 Analysis Lab": "modules.analysis_lab",
    "⚙️ API Setup": "modules.api_setup",
}

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:16px 0 8px 0;">
        <div style="font-size:28px; font-weight:700; color:{Palette.TEXT_PRIMARY}; letter-spacing:-1px;">
            ◆ Market Intelligence Tool
        </div>
        <div style="font-size:11px; color:{Palette.TEXT_MUTED}; letter-spacing:2px; text-transform:uppercase; margin-top:4px;">
            Institutional-Grade Analytics
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    selected_page = st.radio(
        "Navigation",
        list(PAGE_MODULES.keys()),
        index=0,
        key="nav_radio",
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Watchlist quick view
    try:
        from data.watchlist import get_watchlist
        wl = get_watchlist()
        if not wl.empty:
            st.markdown(f"**★ Watchlist** ({len(wl)})")
            for _, row in wl.head(8).iterrows():
                st.markdown(
                    f'<span style="color:{Palette.TEXT_SECONDARY}; font-size:12px;">• {row["symbol"]}</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<span style="color:{Palette.TEXT_MUTED}; font-size:12px;">★ Watchlist empty</span>',
                unsafe_allow_html=True,
            )
    except Exception:
        st.markdown(
            f'<span style="color:{Palette.TEXT_MUTED}; font-size:12px;">★ Watchlist</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", key="global_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.markdown(
            f'<div style="color:{Palette.TEXT_MUTED}; font-size:10px; padding-top:10px;">v1.0.0</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="font-size:10px;color:#64748b;font-family:JetBrains Mono,monospace;text-align:center;margin-top:8px;">'
        f'{datetime.now().strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )

# ── Main Content Area ───────────────────────────────────────
try:
    module_path = PAGE_MODULES[selected_page]
    module = importlib.import_module(module_path)
    module.render()
except Exception as e:
    logger.error(f"Page render error: {e}", exc_info=True)
    st.error(f"Error loading page: {e}")
    st.info("Check API configuration on the ⚙️ API Setup page, or review nexus.log for details.")
