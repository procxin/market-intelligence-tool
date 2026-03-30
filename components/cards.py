"""
Market Intelligence Tool — Card Components
==================================
Professional metric cards, status tiles, and info blocks.
"""

from __future__ import annotations
import streamlit as st
from theme import Palette
from utils.formatting import fmt_number, fmt_pct, color_for_value, delta_icon


def metric_card(label: str, value: str, delta: float | None = None, delta_suffix: str = "%", source: str = ""):
    """Render a styled metric card using st.markdown."""
    delta_html = ""
    if delta is not None:
        color = color_for_value(delta)
        icon = delta_icon(delta)
        delta_html = f'<p style="color:{color}; font-size:13px; font-weight:600; margin:4px 0 0 0;">{icon} {delta:+.2f}{delta_suffix}</p>'

    source_html = ""
    if source:
        source_html = f'<p style="font-size:10px; color:{Palette.TEXT_MUTED}; font-family:monospace; margin:6px 0 0 0; opacity:0.7;">{source}</p>'

    st.markdown(
        f'<div style="background:{Palette.BG_CARD}; border:1px solid {Palette.BORDER}; border-radius:10px; padding:16px 20px; margin-bottom:8px;">'
        f'<p style="color:{Palette.TEXT_SECONDARY}; font-size:12px; text-transform:uppercase; letter-spacing:0.5px; margin:0 0 4px 0;">{label}</p>'
        f'<p style="color:{Palette.TEXT_PRIMARY}; font-size:22px; font-weight:700; margin:0;">{value}</p>'
        f'{delta_html}'
        f'{source_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a module section header."""
    icon_html = f'<span style="margin-right:8px;">{icon}</span>' if icon else ""
    sub_html = f'<div style="color:{Palette.TEXT_SECONDARY}; font-size:14px; margin-top:4px;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="margin-bottom:16px;">
        <div style="color:{Palette.TEXT_PRIMARY}; font-size:20px; font-weight:700;">{icon_html}{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def status_badge(text: str, color: str = Palette.ACCENT_TEAL):
    """Inline status badge."""
    return f'<span style="background:{color}22; color:{color}; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600;">{text}</span>'


def risk_gauge(level: str) -> str:
    """Return colored risk level HTML."""
    colors = {
        "Low": Palette.GREEN,
        "Medium": Palette.AMBER,
        "High": Palette.ORANGE,
        "Critical": Palette.RED,
    }
    color = colors.get(level, Palette.TEXT_MUTED)
    return f'<span style="color:{color}; font-weight:700;">● {level}</span>'


def data_table_with_colors(df, value_col: str = "pct_change"):
    """Display a DataFrame with colored values."""
    if df.empty:
        st.info("No data available")
        return

    def color_row(row):
        val = row.get(value_col, 0)
        if isinstance(val, (int, float)):
            color = color_for_value(val)
            return [f"color: {color}"] * len(row)
        return [""] * len(row)

    styled = df.style.apply(color_row, axis=1).format(
        {col: "{:.2f}" for col in df.select_dtypes(include=["float64", "float32"]).columns}
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)


def api_status_indicator(name: str, is_configured: bool):
    """Show API key status."""
    if is_configured:
        st.markdown(f"✅ **{name}** — Connected", unsafe_allow_html=True)
    else:
        st.markdown(f"⬜ **{name}** — Not configured", unsafe_allow_html=True)


def empty_state(message: str = "No data available", icon: str = "📭"):
    """Empty state placeholder."""
    st.markdown(f"""
    <div style="text-align:center; padding:40px 20px; color:{Palette.TEXT_MUTED};">
        <div style="font-size:48px; margin-bottom:12px;">{icon}</div>
        <div style="font-size:14px;">{message}</div>
    </div>
    """, unsafe_allow_html=True)
