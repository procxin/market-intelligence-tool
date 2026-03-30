"""
Market Intelligence Tool — Watchlist Manager
====================================
Persistent watchlist stored in DuckDB.
"""

from __future__ import annotations
import time
import logging

import duckdb
import pandas as pd

from config import DB_PATH

logger = logging.getLogger("nexus.watchlist")


def _conn():
    c = duckdb.connect(str(DB_PATH))
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol VARCHAR PRIMARY KEY,
            name VARCHAR,
            asset_type VARCHAR DEFAULT 'equity',
            added_at DOUBLE
        )
    """)
    return c


def get_watchlist() -> pd.DataFrame:
    try:
        c = _conn()
        df = c.execute("SELECT * FROM watchlist ORDER BY added_at DESC").df()
        c.close()
        return df
    except Exception as e:
        logger.error(f"Watchlist read error: {e}")
        return pd.DataFrame(columns=["symbol", "name", "asset_type", "added_at"])


def add_to_watchlist(symbol: str, name: str = "", asset_type: str = "equity") -> bool:
    try:
        c = _conn()
        c.execute(
            "INSERT OR REPLACE INTO watchlist (symbol, name, asset_type, added_at) VALUES (?, ?, ?, ?)",
            [symbol.upper(), name, asset_type, time.time()],
        )
        c.close()
        return True
    except Exception as e:
        logger.error(f"Watchlist add error: {e}")
        return False


def remove_from_watchlist(symbol: str) -> bool:
    try:
        c = _conn()
        c.execute("DELETE FROM watchlist WHERE symbol = ?", [symbol.upper()])
        c.close()
        return True
    except Exception as e:
        logger.error(f"Watchlist remove error: {e}")
        return False


def is_in_watchlist(symbol: str) -> bool:
    try:
        c = _conn()
        result = c.execute("SELECT 1 FROM watchlist WHERE symbol = ?", [symbol.upper()]).fetchone()
        c.close()
        return result is not None
    except Exception:
        return False
