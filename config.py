"""
Market Intelligence Tool — Central Configuration
========================================
All API keys, asset universe definitions, refresh intervals,
and application constants live here.
"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ───────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")


def _get_key(name: str) -> str:
    """Read API key from Streamlit secrets (cloud) or .env (local)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, "")


class _APIKeysMeta(type):
    _KEY_MAP = {
        "FMP": "FMP_API_KEY",
        "FINNHUB": "FINNHUB_API_KEY",
        "ALPHA_VANTAGE": "ALPHA_VANTAGE_API_KEY",
        "FRED": "FRED_API_KEY",
        "COINGECKO": "COINGECKO_API_KEY",
        "NEWSDATA": "NEWSDATA_API_KEY",
        "POLYGON": "POLYGON_API_KEY",
    }

    def __getattr__(cls, name):
        if name in cls._KEY_MAP:
            return _get_key(cls._KEY_MAP[name])
        raise AttributeError(name)


class APIKeys(metaclass=_APIKeysMeta):
    @classmethod
    def status(cls) -> dict[str, bool]:
        return {
            "FMP": bool(cls.FMP),
            "Finnhub": bool(cls.FINNHUB),
            "Alpha Vantage": bool(cls.ALPHA_VANTAGE),
            "FRED": bool(cls.FRED),
            "CoinGecko": bool(cls.COINGECKO),
            "NewsData": bool(cls.NEWSDATA),
            "Polygon": bool(cls.POLYGON),
        }

REFRESH_PRICES = 60
REFRESH_NEWS = 300
REFRESH_MACRO = 900
REFRESH_CRYPTO = 120

MAJOR_INDICES = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
    "STOXX 600": "^STOXX",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "Shanghai Comp": "000001.SS",
}

COMMODITIES = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil (WTI)": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F",
    "Wheat": "ZW=F",
    "Corn": "ZC=F",
}

FX_PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "DXY": "DX-Y.NYB",
}

BONDS = {
    "US 2Y": "^IRX",
    "US 10Y": "^TNX",
    "US 30Y": "^TYX",
}

CRYPTO_IDS = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "Avalanche": "avalanche-2",
    "Cardano": "cardano",
    "Polkadot": "polkadot",
    "Chainlink": "chainlink",
    "Polygon": "matic-network",
}

VOLATILITY = {
    "VIX": "^VIX",
    "VIX 9D": "^VIX9D",
    "VVIX": "^VVIX",
}

FRED_SERIES = {
    "Fed Funds Rate": "FEDFUNDS",
    "SOFR": "SOFR",
    "EFFR": "EFFR",
    "2Y Treasury": "DGS2",
    "10Y Treasury": "DGS10",
    "30Y Treasury": "DGS30",
    "2s10s Spread": "T10Y2Y",
    "10Y-3M Spread": "T10Y3M",
    "TED Spread": "TEDRATE",
    "ICE BofA HY OAS": "BAMLH0A0HYM2",
    "ICE BofA IG OAS": "BAMLC0A4CBBB",
    "Fed Balance Sheet": "WALCL",
    "M2 Money Supply": "M2SL",
    "CPI YoY": "CPIAUCSL",
    "Core PCE": "PCEPILFE",
    "Unemployment Rate": "UNRATE",
    "Initial Claims": "ICSA",
    "ISM Manufacturing": "MANEMP",
    "Consumer Sentiment": "UMCSENT",
    "Real GDP": "GDPC1",
    "Commercial Paper": "DTBSPCKM",
}

SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Energy": "XLE",
    "Consumer Disc.": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication": "XLC",
}

GEO_KEYWORDS = [
    "Taiwan strait", "Ukraine war", "Middle East escalation",
    "Iran sanctions", "China stimulus", "US fiscal cliff",
    "Fed pivot", "OPEC cuts", "trade war", "debt ceiling",
    "banking crisis", "currency crisis", "sovereign default",
    "NATO expansion", "nuclear", "cyber attack", "election",
]

APP_NAME = "Market Intelligence Tool"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Institutional Analytics Platform"
DB_PATH = Path(__file__).parent / "nexus_cache.db"
