import pandas as pd

from strategy_layer.ui.backtest_service import BacktestService


class FakePriceClient:
    def fetch_historical_prices(self, ticker, start_date=None, end_date=None):
        return pd.DataFrame(
            {"Close": [100.0, 105.0, 110.0, 100.0]},
            index=pd.date_range("2024-01-01", periods=4),
        )


class FakePairPriceClient(FakePriceClient):
    pass


def test_backtest_service_exposes_signal_breakdown():
    run = BacktestService(FakePriceClient()).run(
        "AAPL", "noise_band", "2024-01-01", "2024-01-05",
        1000.0, 5.0, {"window": 2, "num_std": 1.0},
    )
    assert run.ticker == "AAPL"
    assert {"close", "position", "upper_band", "lower_band", "signal_reason"} <= set(run.signals)
    assert len(run.result.equity) == 4


def test_backtest_service_supports_pair_strategy():
    run = BacktestService(FakePairPriceClient()).run(
        "AAPL", "stat_arb", "2024-01-01", "2024-01-05",
        1000.0, 5.0, {"other_ticker": "MSFT", "lookback": 2, "entry_z": 1.0},
    )
    assert "signal_reason" in run.signals
