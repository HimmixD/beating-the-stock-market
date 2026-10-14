# Architecture Overview

Quantitative stock analysis project with a point-in-time (PIT) data layer.

## Directory Layout

```
src/pit_layer/         # Core PIT data layer
  cache/               # SQLite persistence (SQLiteStore)
  clients/             # External API clients (SEC, OpenBB, yfinance)
  providers/           # Data-fetching + PIT logic
  router.py            # Entry point: PitRouter
  utils.py             # Concept name mapping for SEC XBRL tags
tests/                 # Test suite (mostly integration tests)
scripts/               # Scratch / usage examples
docs/                  # Reports and archived notes
graphify-out/          # Generated dependency graph (Graphify)
```

## Data Flow

1. `PitRouter.get_value(ticker, concept, year, period, as_of_date)` routes the request.
2. US tickers (no exchange suffix / no dot) go to `SecProvider`.
3. Non-US tickers go to `GlobalProvider` (OpenBB/yfinance).
4. Each provider fetches data, normalizes it, and writes it to `SQLiteStore`.
5. `SQLiteStore.get_pit_value(...)` returns the newest row with `accepted <= as_of_date`.
6. Without `as_of_date`, the latest value is returned and flagged as look-ahead warning.

## Key Components

| File | Responsibility |
|------|----------------|
| `router.py` | Ticker classification, request routing |
| `providers/sec_provider.py` | SEC companyfacts, CIK lookup, concept mapping |
| `providers/global_provider.py` | OpenBB/yfinance fundamentals for non-US tickers |
| `providers/actions_provider.py` | Stock splits via yfinance |
| `cache/sqlite_store.py` | SQLite schema, PIT filter, splits cache |
| `clients/sec_client.py` | Rate-limited SEC API client |
| `clients/openbb_client.py` | OpenBB wrapper |
| `clients/price_client.py` | yfinance OHLCV + splits |
| `utils.py` | `SEC_CONCEPT_MAP` for XBRL → friendly concept names |

## Conventions

- All tickers are upper-cased before lookup.
- Concepts are lower-case on input and mapped to SEC XBRL tag names.
- `database.db` is a local SQLite file; it must not be committed.
- `pytest` is the test runner; most tests hit real APIs and need `SEC_USER_AGENT` in `.env`.
