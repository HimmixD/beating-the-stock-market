import pandas as pd
import pytest

from strategy_layer.backtesting.engine import BacktestEngine


class BuyAndHold:
    def generate_signals(self, data):
        return pd.Series(1.0, index=data.index)


def test_engine_shifts_signal_and_applies_costs():
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    data = pd.DataFrame({"Close": [100.0, 110.0, 121.0]}, index=dates)
    result = BacktestEngine(initial_capital=100.0, transaction_cost_bps=100).run(
        data, BuyAndHold()
    )

    assert result.positions.iloc[0] == 0.0
    assert result.positions.iloc[1] == 1.0
    assert result.equity.iloc[-1] == pytest.approx(119.90)
    assert result.total_return == pytest.approx(0.199)


def test_engine_rejects_unsorted_or_missing_close():
    dates = pd.to_datetime(["2024-01-02", "2024-01-01"])
    with pytest.raises(ValueError):
        BacktestEngine().run(pd.DataFrame({"Close": [1, 2]}, index=dates), BuyAndHold())
    with pytest.raises(ValueError):
        BacktestEngine().run(pd.DataFrame({"Open": [1, 2]}, index=dates), BuyAndHold())
