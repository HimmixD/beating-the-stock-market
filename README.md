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
public CSV endpoint is supported and its observation date is used as the
availability lower bound; production PIT studies should therefore configure the
API key. Backtests shift generated signals by one daily bar to prevent
same-bar look-ahead and apply turnover costs.