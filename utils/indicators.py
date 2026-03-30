"""
Market Intelligence Tool — Technical & Macro Indicators
================================================
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, window: int = 20, std_dev: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    middle = sma(series, window)
    std = series.rolling(window=window).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def z_score(series: pd.Series, window: int = 252) -> pd.Series:
    mean = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    return (series - mean) / std.replace(0, np.nan)


def drawdown(series: pd.Series) -> pd.Series:
    peak = series.expanding().max()
    dd = (series - peak) / peak
    return dd


def correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    returns = df.pct_change().dropna()
    return returns.corr(method=method)


def volatility(series: pd.Series, window: int = 21, annualize: bool = True) -> pd.Series:
    returns = series.pct_change()
    vol = returns.rolling(window=window).std()
    if annualize:
        vol = vol * np.sqrt(252)
    return vol


def regime_indicator(vix_series: pd.Series) -> pd.Series:
    """Simple vol regime: low (<15), normal (15-25), high (25-35), crisis (>35)."""
    conditions = [
        vix_series < 15,
        (vix_series >= 15) & (vix_series < 25),
        (vix_series >= 25) & (vix_series < 35),
        vix_series >= 35,
    ]
    labels = ["Low Vol", "Normal", "High Vol", "Crisis"]
    return pd.Series(np.select(conditions, labels, default="Unknown"), index=vix_series.index)
