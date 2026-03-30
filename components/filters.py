"""
Market Intelligence Tool — Shared Filters
=================================
Reusable filter widgets.
"""

from __future__ import annotations
import streamlit as st
from datetime import datetime, timedelta


def time_range_selector(key: str = "time_range") -> str:
    """Returns period string for yfinance or days count."""
    options = {
        "1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo",
        "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "Max": "max"
    }
    selected = st.radio(
        "Time Range",
        options=list(options.keys()),
        horizontal=True,
        key=key,
        index=6,  # default 1Y
    )
    return options[selected]


def date_range_picker(key: str = "date_range", default_days: int = 30) -> tuple:
    """Date range picker returning (from_date, to_date) strings."""
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input(
            "From", value=datetime.now() - timedelta(days=default_days), key=f"{key}_from"
        )
    with col2:
        to_date = st.date_input("To", value=datetime.now(), key=f"{key}_to")
    return from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")


def ticker_search(key: str = "ticker_search", label: str = "Enter Ticker") -> str:
    """Ticker input with uppercase normalization."""
    ticker = st.text_input(label, key=key, placeholder="e.g., AAPL, MSFT, TSLA")
    return ticker.upper().strip() if ticker else ""


def multi_ticker_input(key: str = "multi_ticker", label: str = "Tickers (comma-separated)") -> list[str]:
    """Multiple ticker input."""
    raw = st.text_input(label, key=key, placeholder="AAPL, MSFT, GOOGL")
    if raw:
        return [t.strip().upper() for t in raw.split(",") if t.strip()]
    return []
