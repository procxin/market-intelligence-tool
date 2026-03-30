# ◆ Market Intelligence Tool — Institutional Analytics Platform

> **The single pane of glass that every PM opens first thing in the morning.**

Unified, institutional-grade Streamlit platform aggregating macro, micro, liquidity, geopolitical, crypto, and sentiment signals across 9 core modules. Professional dark-mode Plotly visualizations, DuckDB caching, multi-API fallback chains, modular Python architecture.

---

## Quick Start

```bash
cd market-intelligence-tool
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Edit with your API keys
streamlit run app.py
```

Runs in **demo mode** with zero API keys (yfinance fallback). Add keys incrementally.

---

## Modules

| Module | Description |
|--------|-------------|
| 🌍 Market Overview | Indices, commodities, FX, bonds, volatility, sector ETFs, multi-asset comparison |
| 🏦 Liquidity & Funding | SOFR, EFFR, yield curves, credit spreads, Fed balance sheet, M2, early warnings |
| 🌐 Geopolitical Risk | News scored by impact, keyword scanner, regional risk matrix, event database |
| 📅 Catalyst Calendar | Earnings, FOMC, CPI, GDP, OPEC with impact scoring and countdowns |
| 🏢 Company Deep Dive | Fundamentals, Bollinger/RSI/MACD technicals, news sentiment |
| ₿ Digital Assets | Crypto prices, historical charts, cross-asset correlation matrix |
| 📰 News & Sentiment | AI-scored news feed, catalyst watchlist with alerts |
| 🔬 Analysis Lab | Chart builder, correlation matrix, stress tester, CSV export |
| ⚙️ API Setup | Connection status, setup guides, system health |

---

## API Keys

All loaded from `.env`. None required — app degrades gracefully.

| Provider | Variable | Free Tier | Priority |
|----------|----------|-----------|----------|
| FRED | `FRED_API_KEY` | Unlimited | ⭐⭐⭐ Critical |
| FMP | `FMP_API_KEY` | 250/day | ⭐⭐⭐ High |
| Finnhub | `FINNHUB_API_KEY` | 60/min | ⭐⭐⭐ High |
| CoinGecko | `COINGECKO_API_KEY` | 10-30/min | ⭐⭐ High |
| Alpha Vantage | `ALPHA_VANTAGE_API_KEY` | 25/day | ⭐⭐ Medium |
| NewsData | `NEWSDATA_API_KEY` | 200/day | ⭐ Low |
| Polygon | `POLYGON_API_KEY` | 5/min | ⭐ Optional |

---

## Project Structure

```
market-intelligence-tool/
├── app.py                    # Entry + navigation
├── config.py                 # Keys, assets, constants
├── theme.py                  # Dark Plotly template + CSS
├── data/
│   ├── api_clients.py        # FMP, Finnhub, FRED, CoinGecko, yfinance
│   ├── cache.py              # DuckDB + in-memory TTL
│   └── watchlist.py          # Persistent watchlist
├── pages/                    # 9 module pages
├── components/               # Cards, charts, filters
└── utils/                    # Formatting, indicators, scoring
```

## Data Flow

```
API → Retry → Memory Cache (TTL) + DuckDB → UI with [Source — Freshness] watermark
```

Fallbacks: Prices (FMP→yfinance), News (FMP→Finnhub→NewsData), Crypto (CoinGecko→yfinance)

---

## Extending

**New API:** Add key to `config.py` + wrapper in `data/api_clients.py` + integrate via `cached_fetch()`.
**New Page:** Create `pages/my_page.py` with `def render():` + register in `app.py` PAGE_MODULES.
**New Indicator:** Add to `utils/indicators.py` (Series in → Series out).

## Deploy

**Docker:** `FROM python:3.11-slim` → install requirements → `streamlit run app.py`
**Streamlit Cloud:** Push to GitHub, add secrets as TOML.

## Roadmap

Snowflake integration · LangChain AI Co-Pilot · WebSocket streaming · Options flow scanner · Alerting (Slack/Telegram) · Portfolio tracker · Backtesting engine · Bloomberg BQL bridge
