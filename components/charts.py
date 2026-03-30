"""
Market Intelligence Tool — Chart Components
====================================
Reusable Plotly chart builders with institutional styling.
"""

from __future__ import annotations
from typing import Optional

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from theme import Palette


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    """Convert hex color to rgba() string that Plotly accepts."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def price_chart(
    df: pd.DataFrame,
    title: str = "",
    date_col: str = "Date",
    value_col: str = "Close",
    show_volume: bool = False,
    height: int = 400,
) -> go.Figure:
    """Line chart for price series with optional volume."""
    fig = go.Figure()

    color = Palette.ACCENT_BLUE
    fig.add_trace(go.Scatter(
        x=df[date_col] if date_col in df.columns else df.index,
        y=df[value_col],
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba(59, 130, 246, 0.08)",
        name=value_col,
    ))

    fig.update_layout(
        title=title,
        height=height,
        showlegend=False,
        xaxis_title="",
        yaxis_title="",
    )
    return fig


def candlestick_chart(
    df: pd.DataFrame,
    title: str = "",
    height: int = 450,
) -> go.Figure:
    """OHLC candlestick chart."""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        increasing_line_color=Palette.GREEN,
        decreasing_line_color=Palette.RED,
        increasing_fillcolor=Palette.GREEN,
        decreasing_fillcolor=Palette.RED,
    )])
    fig.update_layout(
        title=title,
        height=height,
        xaxis_rangeslider_visible=False,
    )
    return fig


def multi_line_chart(
    df: pd.DataFrame,
    columns: list[str],
    title: str = "",
    height: int = 400,
    normalize: bool = False,
) -> go.Figure:
    """Multi-series line chart."""
    fig = go.Figure()
    for i, col in enumerate(columns):
        y = df[col]
        if normalize and len(y) > 0:
            y = (y / y.iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(
            x=df.index,
            y=y,
            mode="lines",
            line=dict(color=Palette.SERIES[i % len(Palette.SERIES)], width=2),
            name=col,
        ))
    fig.update_layout(
        title=title,
        height=height,
        yaxis_title="% Change" if normalize else "",
    )
    return fig


def bar_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
    horizontal: bool = False,
    height: int = 400,
    color_by_value: bool = True,
) -> go.Figure:
    """Bar chart with optional value-based coloring."""
    if color_by_value:
        colors = [Palette.GREEN if v >= 0 else Palette.RED for v in values]
    else:
        colors = [Palette.ACCENT_BLUE] * len(values)

    if horizontal:
        fig = go.Figure(go.Bar(
            y=labels, x=values, orientation="h",
            marker_color=colors,
            text=[f"{v:+.2f}%" for v in values],
            textposition="outside",
            textfont=dict(size=11),
        ))
    else:
        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=colors,
            text=[f"{v:+.2f}%" for v in values],
            textposition="outside",
            textfont=dict(size=11),
        ))

    fig.update_layout(title=title, height=height, showlegend=False)
    return fig


def heatmap(
    matrix: pd.DataFrame,
    title: str = "",
    height: int = 500,
    color_scale: str = "RdBu_r",
    zmin: float = -1,
    zmax: float = 1,
) -> go.Figure:
    """Correlation / heatmap chart."""
    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        colorscale=color_scale,
        zmin=zmin, zmax=zmax,
        text=np.round(matrix.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=10),
        colorbar=dict(title="Corr"),
    ))
    fig.update_layout(title=title, height=height)
    return fig


def gauge_chart(value: float, title: str = "", min_val: float = 0, max_val: float = 100, height: int = 250) -> go.Figure:
    """Gauge / speedometer chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(size=14, color=Palette.TEXT_SECONDARY)),
        number=dict(font=dict(size=28, color=Palette.TEXT_PRIMARY)),
        gauge=dict(
            axis=dict(range=[min_val, max_val], tickcolor=Palette.TEXT_MUTED),
            bar=dict(color=Palette.ACCENT_BLUE),
            bgcolor=Palette.BG_SECONDARY,
            bordercolor=Palette.BORDER,
            steps=[
                dict(range=[min_val, max_val * 0.3], color=_hex_to_rgba(Palette.GREEN, 0.2)),
                dict(range=[max_val * 0.3, max_val * 0.7], color=_hex_to_rgba(Palette.AMBER, 0.2)),
                dict(range=[max_val * 0.7, max_val], color=_hex_to_rgba(Palette.RED, 0.2)),
            ],
        ),
    ))
    fig.update_layout(height=height)
    return fig


def treemap(
    labels: list[str],
    parents: list[str],
    values: list[float],
    colors: list[float] | None = None,
    title: str = "",
    height: int = 500,
) -> go.Figure:
    """Treemap for sector/market cap visualization."""
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            colorscale="RdYlGn",
            cmid=0,
        ) if colors else {},
        textinfo="label+value+percent entry",
        textfont=dict(size=12),
    ))
    fig.update_layout(title=title, height=height)
    return fig


def area_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    color: str = Palette.ACCENT_TEAL,
    height: int = 350,
) -> go.Figure:
    """Simple area chart."""
    fig = go.Figure(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        fill="tozeroy",
        fillcolor=_hex_to_rgba(color, 0.1),
        line=dict(color=color, width=2),
    ))
    fig.update_layout(title=title, height=height, showlegend=False)
    return fig
