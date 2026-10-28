import pandas as pd

from strategy_layer.risk.regime_filter import Regime, RegimeFilter
from strategy_layer.strategies.templates import (
    NoiseBandStrategy, OvernightEffectStrategy, StatArbStrategy,
)


def test_regime_filter_disables_crisis():
    dates = pd.date_range("2024-01-01", periods=21)
    macro = pd.DataFrame({"DXY": [100.0] * 20 + [110.0], "DFF": [2.0] * 21}, index=dates)
    regimes = RegimeFilter().classify(macro)
    assert regimes.iloc[-1] == Regime.CRISIS.value
    assert not RegimeFilter().is_enabled(macro).iloc[-1]


def test_strategy_templates_return_aligned_signals():
    dates = pd.date_range("2024-01-01", periods=10)
    data = pd.DataFrame({"Close": range(100, 110)}, index=dates)
    assert OvernightEffectStrategy().generate_signals(data).eq(1.0).all()
    assert NoiseBandStrategy(window=3).generate_signals(data).index.equals(dates)
    pair = StatArbStrategy(data["Close"] * 1.01, lookback=3).generate_signals(data)
    assert pair.index.equals(dates)
