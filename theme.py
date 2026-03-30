"""
Market Intelligence Tool — Professional Dark Theme
==========================================
Institutional-grade color palette, Plotly template,
and Streamlit CSS injection.
"""

from __future__ import annotations
import plotly.graph_objects as go
import plotly.io as pio

# ── Color Palette ───────────────────────────────────────────
class Palette:
    # Backgrounds
    BG_PRIMARY = "#0a0e17"
    BG_SECONDARY = "#111827"
    BG_CARD = "#151c2c"
    BG_CARD_HOVER = "#1a2235"
    BG_INPUT = "#1e2a3a"

    # Text
    TEXT_PRIMARY = "#e2e8f0"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    # Accents
    ACCENT_BLUE = "#3b82f6"
    ACCENT_TEAL = "#14b8a6"
    ACCENT_CYAN = "#06b6d4"
    ACCENT_INDIGO = "#6366f1"
    ACCENT_PURPLE = "#8b5cf6"

    # Semantic
    GREEN = "#10b981"
    RED = "#ef4444"
    AMBER = "#f59e0b"
    ORANGE = "#f97316"

    # Chart series
    SERIES = [
        "#3b82f6", "#14b8a6", "#f59e0b", "#ef4444",
        "#8b5cf6", "#06b6d4", "#ec4899", "#f97316",
        "#84cc16", "#6366f1", "#22d3ee", "#a855f7",
    ]

    # Borders
    BORDER = "#1e293b"
    BORDER_LIGHT = "#334155"

    # Gradients (CSS)
    GRADIENT_HEADER = "linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)"


def get_plotly_template() -> go.layout.Template:
    """Create the institutional dark Plotly template."""
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor=Palette.BG_CARD,
        plot_bgcolor=Palette.BG_CARD,
        font=dict(
            family="'DM Sans', 'Segoe UI', sans-serif",
            color=Palette.TEXT_PRIMARY,
            size=12,
        ),
        title=dict(
            font=dict(size=16, color=Palette.TEXT_PRIMARY),
            x=0.0, xanchor="left",
        ),
        xaxis=dict(
            gridcolor=Palette.BORDER,
            zerolinecolor=Palette.BORDER,
            linecolor=Palette.BORDER,
            tickfont=dict(color=Palette.TEXT_SECONDARY, size=10),
            title_font=dict(color=Palette.TEXT_SECONDARY, size=11),
        ),
        yaxis=dict(
            gridcolor=Palette.BORDER,
            zerolinecolor=Palette.BORDER,
            linecolor=Palette.BORDER,
            tickfont=dict(color=Palette.TEXT_SECONDARY, size=10),
            title_font=dict(color=Palette.TEXT_SECONDARY, size=11),
        ),
        colorway=Palette.SERIES,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=Palette.TEXT_SECONDARY, size=10),
        ),
        margin=dict(l=50, r=20, t=50, b=40),
        hoverlabel=dict(
            bgcolor=Palette.BG_SECONDARY,
            font_size=12,
            font_color=Palette.TEXT_PRIMARY,
            bordercolor=Palette.BORDER_LIGHT,
        ),
    )
    return template


def register_theme():
    """Register our template as the default Plotly theme."""
    pio.templates["nexus"] = get_plotly_template()
    pio.templates.default = "nexus"


# ── Streamlit CSS Injection ─────────────────────────────────
STREAMLIT_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global ─────────────────────────────────────── */
.stApp {{
    background: {Palette.BG_PRIMARY};
    font-family: 'DM Sans', sans-serif;
}}

.stApp header {{
    background: {Palette.BG_PRIMARY} !important;
    border-bottom: 1px solid {Palette.BORDER};
}}

/* ── Sidebar ────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: {Palette.BG_SECONDARY} !important;
    border-right: 1px solid {Palette.BORDER};
}}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {{
    color: {Palette.TEXT_PRIMARY};
}}

/* ── Cards / Containers ─────────────────────────── */
div[data-testid="stExpander"],
div[data-testid="stMetric"] {{
    background: {Palette.BG_CARD};
    border: 1px solid {Palette.BORDER};
    border-radius: 8px;
}}

div[data-testid="stMetric"] label {{
    color: {Palette.TEXT_SECONDARY} !important;
}}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
    color: {Palette.TEXT_PRIMARY} !important;
    font-weight: 600;
}}

/* ── Tabs ────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 16px;
    background: {Palette.BG_SECONDARY};
    border-radius: 8px;
    padding: 8px 12px;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {Palette.TEXT_SECONDARY};
    border-radius: 6px;
    font-weight: 500;
    font-size: 13px;
    padding: 10px 22px !important;
}}

.stTabs [aria-selected="true"] {{
    background: {Palette.BG_CARD} !important;
    color: {Palette.ACCENT_BLUE} !important;
}}

/* ── DataFrames ──────────────────────────────────── */
.stDataFrame {{
    border: 1px solid {Palette.BORDER};
    border-radius: 8px;
}}

/* ── Buttons ─────────────────────────────────────── */
.stButton > button {{
    background: {Palette.BG_INPUT};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_LIGHT};
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s;
}}

.stButton > button:hover {{
    background: {Palette.ACCENT_BLUE};
    border-color: {Palette.ACCENT_BLUE};
    color: white;
}}

/* ── Metric delta colors ─────────────────────────── */
div[data-testid="stMetricDelta"] svg {{
    display: inline;
}}

/* ── Input fields ────────────────────────────────── */
.stTextInput input, .stSelectbox select, .stMultiSelect {{
    background: {Palette.BG_INPUT} !important;
    border: 1px solid {Palette.BORDER_LIGHT} !important;
    color: {Palette.TEXT_PRIMARY} !important;
    border-radius: 6px;
}}

/* ── Scrollbar ───────────────────────────────────── */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: {Palette.BG_PRIMARY};
}}
::-webkit-scrollbar-thumb {{
    background: {Palette.BORDER_LIGHT};
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {Palette.TEXT_MUTED};
}}

/* ── Custom metric card class ────────────────────── */
.nexus-card {{
    background: {Palette.BG_CARD};
    border: 1px solid {Palette.BORDER};
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}}

.nexus-card:hover {{
    border-color: {Palette.BORDER_LIGHT};
    background: {Palette.BG_CARD_HOVER};
}}

.nexus-header {{
    background: {Palette.GRADIENT_HEADER};
    border: 1px solid {Palette.BORDER};
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
}}

/* ── Source watermark ────────────────────────────── */
.source-tag {{
    font-size: 10px;
    color: {Palette.TEXT_MUTED};
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
}}

/* ── Positive / Negative ─────────────────────────── */
.val-pos {{ color: {Palette.GREEN}; font-weight: 600; }}
.val-neg {{ color: {Palette.RED}; font-weight: 600; }}
.val-warn {{ color: {Palette.AMBER}; font-weight: 600; }}

</style>
"""


def inject_css():
    """Inject the custom CSS into the Streamlit app."""
    import streamlit as st
    st.markdown(STREAMLIT_CSS, unsafe_allow_html=True)
