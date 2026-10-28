## Quant Layer

The strategy layer is deliberately separate from `PriceClient` and consumes daily
OHLC data through a small strategy protocol:

```text
src/
  pit_layer/
    cache/sqlite_store.py             # PIT cache, including market_observations
    providers/
      macro_provider.py               # FRED (vintages) and DXY
      sentiment_provider.py           # yfinance news and baseline score
  strategy_layer/
    backtesting/engine.py             # delayed-signal daily engine
    risk/position_sizer.py            # fractional Kelly (half-Kelly default)
    risk/regime_filter.py             # DXY/rate regime gating
    strategies/templates.py           # overnight, stat-arb, noise bands
    statistics.py                     # t-test and walk-forward evaluation
tests/
  test_macro_provider.py
  test_backtest_engine.py
  test_quant_support.py
```

`MacroProvider` stores `available_date` separately from the observation date.
With a `FRED_API_KEY`, FRED realtime vintages are used. Without a key, the
public CSV endpoint is supported for exploration only; it does not provide
historical release vintages and must not be used for a strict PIT study.
Backtests shift generated signals by one daily bar to prevent same-bar
look-ahead and apply turnover costs.

## PIT guarantees and limitations

- SEC facts use the filing availability timestamp and preserve reporting
  `start_date`/`end_date`.
- Global fundamentals are accepted only when the upstream record includes a
  publication or filing date. A reporting-period end date is never treated as
  a release date.
- A request with `as_of_date` is PIT-filtered; a request without it is an
  explicitly flagged latest snapshot.
- `database.db` is a local cache and is ignored by Git. It is recreated by
  `SQLiteStore`.
- Network-backed tests should be run explicitly; the default suite includes
  deterministic unit tests and the existing integration coverage.

## Dashboard

Start the local Bloomberg-inspired research terminal with:

```text
streamlit run app.py
```

The dashboard currently provides daily historical backtests, equity and risk
metrics, current position state, and an explainable signal table. New strategies
should be registered in `strategy_layer/ui/backtest_service.py`; this keeps the
UI independent from strategy implementation details.