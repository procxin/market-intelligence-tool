"""
Market Intelligence Tool — API Clients
==============================
Unified wrappers for all data providers.
Each function returns normalized data structures.
Fallback chains: Primary API → Secondary → yfinance.
"""

from __future__ import annotations
import time
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

import requests
import pandas as pd
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import APIKeys

logger = logging.getLogger("nexus.api")

# ── HTTP Helpers ────────────────────────────────────────────
_session = requests.Session()
_session.headers.update({"User-Agent": "Nexus/1.0"})

REQUEST_TIMEOUT = 10


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, max=3),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
)
def _get(url: str, params: dict = None, timeout: int = REQUEST_TIMEOUT) -> dict | list | None:
    """Safe GET with retries."""
    try:
        resp = _session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url}")
        return None
    except Exception as e:
        logger.warning(f"Request error for {url}: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# MARKET DATA — yfinance (always available as base fallback)
# ══════════════════════════════════════════════════════════════

def yf_get_quotes(symbols: dict[str, str]) -> pd.DataFrame:
    """Fetch latest quotes via yfinance. Returns DataFrame with name, symbol, price, change, pct."""
    import yfinance as yf
    rows = []
    tickers_str = " ".join(symbols.values())
    try:
        data = yf.download(tickers_str, period="5d", group_by="ticker", progress=False, threads=True)
        for name, sym in symbols.items():
            try:
                if len(symbols) == 1:
                    df = data
                else:
                    df = data[sym] if sym in data.columns.get_level_values(0) else None
                if df is None or df.empty:
                    continue
                df = df.dropna(subset=["Close"])
                if len(df) < 2:
                    continue
                last = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                chg = last - prev
                pct = (chg / prev * 100) if prev != 0 else 0.0
                rows.append({
                    "name": name,
                    "symbol": sym,
                    "price": round(last, 2),
                    "change": round(chg, 2),
                    "pct_change": round(pct, 2),
                })
            except Exception:
                continue
    except Exception as e:
        logger.error(f"yfinance bulk download error: {e}")
    return pd.DataFrame(rows)


def yf_get_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Get OHLCV history for a single ticker."""
    import yfinance as yf
    try:
        tk = yf.Ticker(symbol)
        df = tk.history(period=period)
        if df.empty:
            return pd.DataFrame()
        df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        logger.error(f"yfinance history error for {symbol}: {e}")
        return pd.DataFrame()


def yf_get_info(symbol: str) -> dict:
    """Get ticker info/fundamentals."""
    import yfinance as yf
    try:
        tk = yf.Ticker(symbol)
        return tk.info or {}
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════
# FMP — Financial Modeling Prep
# ══════════════════════════════════════════════════════════════

def fmp_quote(symbols: list[str]) -> list[dict]:
    """Batch quote from FMP."""
    if not APIKeys.FMP:
        return []
    url = f"https://financialmodelingprep.com/api/v3/quote/{','.join(symbols)}"
    data = _get(url, params={"apikey": APIKeys.FMP})
    return data if isinstance(data, list) else []


def fmp_company_profile(symbol: str) -> dict:
    if not APIKeys.FMP:
        return {}
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
    data = _get(url, params={"apikey": APIKeys.FMP})
    return data[0] if isinstance(data, list) and data else {}


def fmp_financials(symbol: str, statement: str = "income-statement", period: str = "annual") -> list:
    if not APIKeys.FMP:
        return []
    url = f"https://financialmodelingprep.com/api/v3/{statement}/{symbol}"
    data = _get(url, params={"apikey": APIKeys.FMP, "period": period, "limit": 10})
    return data if isinstance(data, list) else []


def fmp_news(tickers: str = "", limit: int = 30) -> list[dict]:
    if not APIKeys.FMP:
        return []
    url = "https://financialmodelingprep.com/api/v3/stock_news"
    params = {"apikey": APIKeys.FMP, "limit": limit}
    if tickers:
        params["tickers"] = tickers
    data = _get(url, params=params)
    return data if isinstance(data, list) else []


def fmp_earnings_calendar(from_date: str = "", to_date: str = "") -> list:
    if not APIKeys.FMP:
        return []
    url = "https://financialmodelingprep.com/api/v3/earning_calendar"
    params = {"apikey": APIKeys.FMP}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    data = _get(url, params=params)
    return data if isinstance(data, list) else []


def fmp_economic_calendar(from_date: str = "", to_date: str = "") -> list:
    if not APIKeys.FMP:
        return []
    url = "https://financialmodelingprep.com/api/v3/economic_calendar"
    params = {"apikey": APIKeys.FMP}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    data = _get(url, params=params)
    return data if isinstance(data, list) else []


def fmp_sector_performance() -> list:
    if not APIKeys.FMP:
        return []
    url = "https://financialmodelingprep.com/api/v3/sector-performance"
    data = _get(url, params={"apikey": APIKeys.FMP})
    return data if isinstance(data, list) else []


# ══════════════════════════════════════════════════════════════
# FINNHUB
# ══════════════════════════════════════════════════════════════

def finnhub_quote(symbol: str) -> dict:
    if not APIKeys.FINNHUB:
        return {}
    url = "https://finnhub.io/api/v1/quote"
    return _get(url, params={"symbol": symbol, "token": APIKeys.FINNHUB}) or {}


def finnhub_news(category: str = "general", min_id: int = 0) -> list:
    if not APIKeys.FINNHUB:
        return []
    url = "https://finnhub.io/api/v1/news"
    data = _get(url, params={"category": category, "minId": min_id, "token": APIKeys.FINNHUB})
    return data if isinstance(data, list) else []


def finnhub_company_news(symbol: str, from_date: str = "", to_date: str = "") -> list:
    if not APIKeys.FINNHUB:
        return []
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://finnhub.io/api/v1/company-news"
    data = _get(url, params={
        "symbol": symbol, "from": from_date, "to": to_date, "token": APIKeys.FINNHUB
    })
    return data if isinstance(data, list) else []


def finnhub_sentiment(symbol: str) -> dict:
    if not APIKeys.FINNHUB:
        return {}
    url = "https://finnhub.io/api/v1/news-sentiment"
    return _get(url, params={"symbol": symbol, "token": APIKeys.FINNHUB}) or {}


def finnhub_earnings_calendar(from_date: str = "", to_date: str = "") -> list:
    if not APIKeys.FINNHUB:
        return []
    if not from_date:
        from_date = datetime.now().strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    url = "https://finnhub.io/api/v1/calendar/earnings"
    data = _get(url, params={"from": from_date, "to": to_date, "token": APIKeys.FINNHUB})
    if isinstance(data, dict):
        return data.get("earningsCalendar", [])
    return []


# ══════════════════════════════════════════════════════════════
# FRED — Federal Reserve Economic Data
# ══════════════════════════════════════════════════════════════

def fred_series(series_id: str, limit: int = 252) -> pd.DataFrame:
    """Fetch FRED time series as DataFrame with 'date' and 'value' columns."""
    if not APIKeys.FRED:
        return pd.DataFrame()
    url = f"https://api.stlouisfed.org/fred/series/observations"
    data = _get(url, params={
        "series_id": series_id,
        "api_key": APIKeys.FRED,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    })
    if not data or "observations" not in data:
        return pd.DataFrame()
    df = pd.DataFrame(data["observations"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["value"]).sort_values("date")
    return df[["date", "value"]]


def fred_latest(series_id: str) -> Optional[float]:
    """Get the most recent value of a FRED series."""
    df = fred_series(series_id, limit=5)
    if df.empty:
        return None
    return float(df["value"].iloc[-1])


# ══════════════════════════════════════════════════════════════
# COINGECKO — Crypto Data
# ══════════════════════════════════════════════════════════════

def cg_prices(ids: list[str], vs: str = "usd") -> dict:
    """Get current prices + 24h change for crypto assets."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs,
        "include_24hr_change": "true",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
    }
    if APIKeys.COINGECKO:
        params["x_cg_demo_key"] = APIKeys.COINGECKO
    return _get(url, params=params) or {}


def cg_market_chart(coin_id: str, days: int = 90, vs: str = "usd") -> pd.DataFrame:
    """Get historical market chart data for a coin."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs, "days": days}
    if APIKeys.COINGECKO:
        params["x_cg_demo_key"] = APIKeys.COINGECKO
    data = _get(url, params=params)
    if not data or "prices" not in data:
        return pd.DataFrame()
    df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["date", "price"]]


def cg_global() -> dict:
    """Get global crypto market data."""
    url = "https://api.coingecko.com/api/v3/global"
    params = {}
    if APIKeys.COINGECKO:
        params["x_cg_demo_key"] = APIKeys.COINGECKO
    data = _get(url, params=params)
    return data.get("data", {}) if isinstance(data, dict) else {}


def cg_trending() -> list:
    """Get trending coins."""
    url = "https://api.coingecko.com/api/v3/search/trending"
    params = {}
    if APIKeys.COINGECKO:
        params["x_cg_demo_key"] = APIKeys.COINGECKO
    data = _get(url, params=params)
    if isinstance(data, dict) and "coins" in data:
        return [c.get("item", {}) for c in data["coins"]]
    return []


# ══════════════════════════════════════════════════════════════
# NEWS — NewsData.io
# ══════════════════════════════════════════════════════════════

def newsdata_latest(query: str = "finance", language: str = "en", size: int = 10) -> list:
    if not APIKeys.NEWSDATA:
        return []
    url = "https://newsdata.io/api/1/latest"
    data = _get(url, params={
        "apikey": APIKeys.NEWSDATA,
        "q": query,
        "language": language,
        "size": size,
        "category": "business",
    })
    if isinstance(data, dict):
        return data.get("results", [])
    return []


# ══════════════════════════════════════════════════════════════
# COMPOSITE / CONVENIENCE
# ══════════════════════════════════════════════════════════════

def get_market_overview(symbols: dict[str, str], source_label: str = "yfinance") -> tuple[pd.DataFrame, str]:
    """
    Fetch market overview — tries FMP first, falls back to yfinance.
    Returns (DataFrame, source_label).
    """
    if APIKeys.FMP:
        try:
            raw = fmp_quote(list(symbols.values()))
            if raw:
                rows = []
                sym_to_name = {v: k for k, v in symbols.items()}
                for q in raw:
                    sym = q.get("symbol", "")
                    rows.append({
                        "name": sym_to_name.get(sym, sym),
                        "symbol": sym,
                        "price": q.get("price", 0),
                        "change": q.get("change", 0),
                        "pct_change": q.get("changesPercentage", 0),
                    })
                if rows:
                    return pd.DataFrame(rows), "FMP"
        except Exception:
            pass
    # Fallback
    df = yf_get_quotes(symbols)
    return df, "yfinance"


def get_news_feed(limit: int = 30) -> tuple[list[dict], str]:
    """Aggregated news — tries FMP → Finnhub → NewsData."""
    # FMP
    news = fmp_news(limit=limit)
    if news:
        normalized = []
        for n in news:
            normalized.append({
                "title": n.get("title", ""),
                "text": n.get("text", "")[:200],
                "url": n.get("url", ""),
                "source": n.get("site", ""),
                "published": n.get("publishedDate", ""),
                "ticker": n.get("symbol", ""),
                "image": n.get("image", ""),
            })
        return normalized, "FMP"

    # Finnhub
    fh_news = finnhub_news(category="general")
    if fh_news:
        normalized = []
        for n in fh_news[:limit]:
            normalized.append({
                "title": n.get("headline", ""),
                "text": n.get("summary", "")[:200],
                "url": n.get("url", ""),
                "source": n.get("source", ""),
                "published": datetime.fromtimestamp(n.get("datetime", 0)).isoformat() if n.get("datetime") else "",
                "ticker": "",
                "image": n.get("image", ""),
            })
        return normalized, "Finnhub"

    # NewsData
    nd = newsdata_latest(query="markets finance economy", size=min(limit, 10))
    if nd:
        normalized = []
        for n in nd:
            normalized.append({
                "title": n.get("title", ""),
                "text": n.get("description", "")[:200] if n.get("description") else "",
                "url": n.get("link", ""),
                "source": n.get("source_id", ""),
                "published": n.get("pubDate", ""),
                "ticker": "",
                "image": n.get("image_url", ""),
            })
        return normalized, "NewsData"

    return [], "none"
