# Architecture Report

Generated during repository cleanup. The source code itself was not changed beyond moving the newer `ActionsProvider` implementation into `providers/` and deleting the duplicate.

## 1. Ghost Files / Redundancies

| File / Directory | Issue | Action Taken |
|------------------|-------|--------------|
| `src/pit_layer/actions_provider.py` | Duplicate of `providers/actions_provider.py`. The "force" fix described in `FIXES_SUMMARY.md` was only present in this orphaned file, while the Router imported the old version. | Copied the newer implementation to `providers/actions_provider.py` and deleted the orphan. |
| `src/__pycache__/test_momentum...pyc` | Ghost artifact from a removed test module. | Deleted. |
| `.btsm_venv/` | Second virtual environment, not the active one (`venv/` is active and contains the editable install). | Deleted. |
| `not _sure/` | Directory contained AI-generated notes and a 9 MB SQLite database tracked by git. The summaries are partly inaccurate. | Markdown files moved to `docs/archive/`. Database removed from git and deleted locally. |
| `scripts/test.py` | Misnamed scratch script; comment mentioned OMV while code queried AAPL. | Renamed to `scripts/scratch_capex.py` and comment fixed. |
| `requirements.txt` | UTF-16 encoded (PowerShell `pip freeze` artifact), ~100 transitive dependencies. | Converted to UTF-8 without content change. |

## 2. Architecture Findings (source code unchanged)

| # | Finding | Severity | Details |
|---|---------|----------|---------|
| 1 | **Fix in wrong file** | High | See redundancy table above. The newer `ActionsProvider` was effectively unused before this cleanup. |
| 2 | **Bug in `utils.py`** | Medium | `_fuzzy_concept_match` references `possible_lower`, which is undefined, and would raise `NameError` if called. The function is currently dead code. |
| 3 | **Look-ahead in GlobalProvider** | High | `GlobalProvider` derives `filed`/`accepted` from `period_ending` (the fiscal period end), not the actual publication date. This violates PIT correctness because fundamentals become available too early. The previous "fix" only added comments. |
| 4 | **Possible data collision in SEC facts** | High (to verify) | Companyfacts returns multiple periods within one filing under the same `fy`/`fp`. The primary key does not include the period `end`/`start`, so `INSERT OR REPLACE` may overwrite rows, and `LIMIT 1` can return a prior-year value. |
| 5 | **Eager router initialization** | Medium | `PitRouter()` instantiates `SecProvider` and `SecClient` immediately. Missing `SEC_USER_AGENT` raises `ValueError` even for split/global-only usage. `load_dotenv()` runs at import time. |
| 6 | **Relative database path** | Medium | `SQLiteStore(db_path="database.db")` resolves relative to the current working directory. Running tests from another directory creates or uses a different database file. |
| 7 | **Tests are integration tests** | Medium | Most tests instantiate `PitRouter()` and hit real networks + the real DB. The `integration` marker exists in `pyproject.toml` but is not used. There are no unit tests for `SQLiteStore`. |
| 8 | **PIT string comparison issues** | Medium | `accepted <= as_of_date` compares full timestamps (e.g. `2023-11-03T23:59:59`) against plain dates (`2023-11-03`). A same-day `as_of_date` excludes filings from that day. Also, SEC `accepted` is synthesized from `filed` because the API does not provide an accepted timestamp; if `filed` is missing, `item.get("filed") + "T23:59:59"` raises `TypeError`. |
| 9 | **Inconsistent providers** | Low | `ActionsProvider` does not inherit from `BaseProvider`. `BaseProvider.get_value` is typed `Optional[float]` but implementations return `dict`. Splits are not PIT-aware. |
| 10 | **Ticker routing heuristic** | Low | `_is_us_ticker` checks international suffixes but then falls back to a simple dot check, making the suffix list redundant for dotted tickers. `BRK.B` is misclassified as non-US. Inputs are not normalized to uppercase before the suffix check. |
| 11 | **Other** | Low | `print()` instead of `logging`; mixed German/English comments; `pyproject.toml` declares no dependencies; `_ensure_cik` saves ~10,000 ticker mappings one by one (slow). |

## 3. Recommendations (out of scope for cleanup)

1. Fix `GlobalProvider` PIT: use actual filing/publication dates, not period end dates.
2. Store the XBRL period `end`/`start` in `financial_facts` and include it in the primary key.
3. Make `SecClient` lazy: only load `.env` and validate `SEC_USER_AGENT` when the client is actually used.
4. Use an absolute or project-root-relative database path.
5. Convert network-dependent tests to integration tests with the `integration` marker and add unit tests with mocks.
6. Replace `print()` with `logging` and normalize language to English for code/comments.
7. Fill `pyproject.toml` project dependencies from `requirements.txt` or switch to a lock file.
