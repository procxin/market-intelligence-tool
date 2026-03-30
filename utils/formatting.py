"""
Market Intelligence Tool — Formatting Utilities
=======================================
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Union, Optional
import math


def fmt_number(n: Union[float, int, None], decimals: int = 2, prefix: str = "", suffix: str = "") -> str:
    """Format number with commas and optional prefix/suffix."""
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    if abs(n) >= 1e12:
        return f"{prefix}{n/1e12:,.{decimals}f}T{suffix}"
    if abs(n) >= 1e9:
        return f"{prefix}{n/1e9:,.{decimals}f}B{suffix}"
    if abs(n) >= 1e6:
        return f"{prefix}{n/1e6:,.{decimals}f}M{suffix}"
    if abs(n) >= 1e4:
        return f"{prefix}{n/1e3:,.{decimals}f}K{suffix}"
    return f"{prefix}{n:,.{decimals}f}{suffix}"


def fmt_pct(n: Union[float, None], decimals: int = 2) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return f"{n:+.{decimals}f}%"


def fmt_currency(n: Union[float, None], currency: str = "$", decimals: int = 2) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return fmt_number(n, decimals=decimals, prefix=currency)


def fmt_delta(n: Union[float, None], decimals: int = 2) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    sign = "+" if n >= 0 else ""
    return f"{sign}{n:,.{decimals}f}"


def fmt_date(dt: Union[str, datetime, None], fmt: str = "%b %d, %Y") -> str:
    if dt is None:
        return "—"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt[:16] if len(dt) > 16 else dt
    return dt.strftime(fmt)


def fmt_time_ago(dt: Union[str, datetime, None]) -> str:
    if dt is None:
        return "—"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt
    if dt.tzinfo:
        from datetime import timezone
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    else:
        return f"{int(seconds // 86400)}d ago"


def color_for_value(val: float) -> str:
    """Return green/red/neutral color string."""
    if val > 0:
        return "#10b981"
    elif val < 0:
        return "#ef4444"
    return "#94a3b8"


def delta_icon(val: float) -> str:
    if val > 0:
        return "▲"
    elif val < 0:
        return "▼"
    return "—"
