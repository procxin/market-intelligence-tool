"""
Market Intelligence Tool — Data Cache Layer
===================================
DuckDB persistent store + in-memory TTL cache.
Every data tile shows source + freshness.
"""

from __future__ import annotations
import time
import json
import logging
import hashlib
from typing import Any, Optional
from pathlib import Path

import duckdb
import pandas as pd

from config import DB_PATH

logger = logging.getLogger("nexus.cache")

# ── In-Memory TTL Cache ─────────────────────────────────────
_mem_cache: dict[str, dict] = {}


def mem_get(key: str, ttl: int = 60) -> Optional[Any]:
    """Get from memory cache if not expired."""
    entry = _mem_cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    return None


def mem_set(key: str, data: Any, source: str = "unknown") -> None:
    """Store in memory cache with timestamp."""
    _mem_cache[key] = {
        "data": data,
        "ts": time.time(),
        "source": source,
    }


def mem_age(key: str) -> Optional[float]:
    """Return seconds since last cache write, or None."""
    entry = _mem_cache.get(key)
    if entry:
        return time.time() - entry["ts"]
    return None


def mem_source(key: str) -> str:
    """Return the data source label."""
    entry = _mem_cache.get(key)
    return entry.get("source", "—") if entry else "—"


def freshness_label(key: str) -> str:
    """Human-readable freshness for display."""
    age = mem_age(key)
    if age is None:
        return "no data"
    if age < 5:
        return "live"
    elif age < 60:
        return f"{int(age)}s ago"
    elif age < 3600:
        return f"{int(age // 60)}m ago"
    else:
        return f"{int(age // 3600)}h ago"


def source_watermark(key: str) -> str:
    """Returns formatted source + freshness for UI."""
    src = mem_source(key)
    fresh = freshness_label(key)
    return f"{src} — {fresh}"


# ── DuckDB Persistent Cache ─────────────────────────────────
def _get_conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kv_cache (
            key VARCHAR PRIMARY KEY,
            value VARCHAR,
            source VARCHAR,
            updated_at DOUBLE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol VARCHAR PRIMARY KEY,
            name VARCHAR,
            asset_type VARCHAR DEFAULT 'equity',
            added_at DOUBLE
        )
    """)
    return conn


def db_get(key: str, ttl: int = 3600) -> Optional[Any]:
    """Get from DuckDB if not expired."""
    try:
        conn = _get_conn()
        result = conn.execute(
            "SELECT value, updated_at FROM kv_cache WHERE key = ?", [key]
        ).fetchone()
        conn.close()
        if result and (time.time() - result[1]) < ttl:
            return json.loads(result[0])
    except Exception as e:
        logger.warning(f"DuckDB read error for {key}: {e}")
    return None


def db_set(key: str, data: Any, source: str = "unknown") -> None:
    """Upsert into DuckDB."""
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO kv_cache (key, value, source, updated_at)
               VALUES (?, ?, ?, ?)""",
            [key, json.dumps(data, default=str), source, time.time()],
        )
        conn.close()
    except Exception as e:
        logger.warning(f"DuckDB write error for {key}: {e}")


# ── Unified fetch-with-cache ─────────────────────────────────
def cached_fetch(
    key: str,
    fetch_fn,
    mem_ttl: int = 60,
    db_ttl: int = 3600,
    source: str = "api",
) -> Optional[Any]:
    """
    Three-tier fetch: memory → DuckDB → live API call.
    Returns data or None.
    """
    # 1. Memory
    data = mem_get(key, ttl=mem_ttl)
    if data is not None:
        return data

    # 2. DuckDB
    data = db_get(key, ttl=db_ttl)
    if data is not None:
        mem_set(key, data, source=f"{source} (db)")
        return data

    # 3. Live fetch
    try:
        data = fetch_fn()
        if data is not None:
            mem_set(key, data, source=source)
            db_set(key, data, source=source)
        return data
    except Exception as e:
        logger.error(f"Fetch error for {key}: {e}")
        return None
