# Pit-Aware Base Layer Analysis Summary

## Project Overview
This is a **quantitative stock analysis project** (quant-project, version 0.1.0) with a **pit-aware (Point in Time) base layer** designed for implementing a market analysis tool.

**Directory Structure:**
- `src/pit_layer/` - Core layer with router, providers, cache, and clients
- `tests/` - Test suite with 7 test files and golden cases CSV
- `database.db` - SQLite database (9MB, pre-populated with data)
- `pyproject.toml` - Project config (source in `src/`, tests in `tests/`)
- `requirements.txt` - Python dependencies (30+ packages)
- `.env` - Contains `SEC_USER_AGENT` for SEC API access

## Core Architecture

### 1. **PitRouter** (`router.py`)
- Routes US tickers (no dot: AAPL, MSFT) → **SecProvider**
- Routes non-US tickers (with dot: EVN.VI, BMW.DE) → **GlobalProvider**
- `_is_us_ticker()` method: simple check ` "." not in ticker`

### 2. **SQLiteStore** (`cache/sqlite_store.py`)
- Three tables: `ticker_mapping`, `financial_facts`, `stock_splits`
- **`get_pit_value()`** - The core PIT method: filters by `accepted <= as_of_date`, orders by `accepted DESC LIMIT 1`
- Prevents look-ahead bias: data only visible after filing date

### 3. **Providers**
- **SecProvider** - SEC API with rate limiting, jitter, CIK lookup, concept mapping
- **GlobalProvider** - OpenBB/yfinance for international fundamentals
- **ActionsProvider** - Stock splits via yfinance

### 4. **Concept Map** (`utils.py`)
- `SEC_CONCEPT_MAP` maps financial concepts to possible names
- e.g., `revenue` → `["Revenues", "SalesRevenueNet", ...]`

## 10 Identified Problems

### 1. **PIT Look-Ahead Bias Gaps**
- `test_pit_time_travel` verifies: querying before filing date returns `None`, after filing returns data with `pit_status="safe_pit"`
- Potential edge cases may allow future data through the `accepted <= ?` filter

### 2. **Global Provider Missing PIT Filtering**
- `global_provider.py` line 46: `accepted = filed_date` as hardcoded fallback
- Means Global provider doesn't properly implement PIT - always uses filed date as "accepted"
- Data filed after `as_of_date` could incorrectly be available

### 3. **Limited Non-US Ticker Coverage**
- Global provider relies on OpenBB/yfinance with limited international coverage
- Test `test_global_provider_routing` must gracefully handle None/errors for tickers like EVN.VI

### 4. **Oversimplified US/Non-US Routing**
- `_is_us_ticker()`: just checks ` "." not in ticker`
- Misses edge cases: some US stocks with dots, some international stocks without dots

### 5. **Incomplete Concept Mapping**
- `SEC_CONCEPT_MAP` covers common concepts but may not match all SEC filing variations
- Fallback to exact concept name may fail to match stored data

### 6. **Stale Split Data**
- `actions_provider` tracks fetched tickers in `self._fetched_tickers` but no refresh mechanism
- Once marked fetched, won't be re-checked

### 7. **Missing Configuration Validation**
- `SecClient` requires `SEC_USER_AGENT` in `.env` (fatal if missing)
- `OpenBBClient` raises `ImportError` if OpenBB not installed
- No graceful degradation

### 8. **PIT Status Oversimplification**
- Both providers set `pit_status` based solely on `as_of_date` presence
- Doesn't account for cache containing data from future filings

### 9. **Schema Inconsistencies**
- Global provider hardcodes `form="ANNUAL"`, `accession=None`
- SEC provider dynamically extracts these from API response
- Causes issues when querying across providers

### 10. **No Data Versioning/Invalidation**
- No mechanism to track data freshness or detect/stale data
- No way to recover if API format changes or data corrupts

## Recommendations for Market Analysis Tool

1. **Fix PIT filtering in Global provider** - properly implement `as_of_date` filtering instead of using filed_date as accepted fallback
2. **Enhance ticker routing** - add exchange/suffix-based detection beyond simple dot-check
3. **Expand concept mapping** - add more variations, implement fuzzy matching
4. **Add data freshness tracking** - timestamp when data was fetched, provide refresh mechanism
5. **Improve error handling** - graceful degradation when APIs/config missing
6. **Normalize PIT status** - make more informative (include filing date, confidence level)
7. **Add comprehensive PIT tests** - extend existing tests with more edge cases
8. **Enable cross-provider querying** - handle schema inconsistencies when comparing data

## Key Insight
The fundamental architecture is **solid** - the PIT concept with `accepted <= as_of_date` filtering in SQLiteStore is correctly implemented and is the right approach. The main implementation gaps are in **edge cases** around international data coverage, routing logic precision, and ensuring the PIT filter works correctly across all providers consistently.

The existing test suite (`test_pit_time_travel`, `test_pit_suit`, `test_golden_cases_csv`) provides good coverage of the PIT functionality and should be the starting point for any enhancements.