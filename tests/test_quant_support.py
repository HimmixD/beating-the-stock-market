import pandas as pd
import pytest

from strategy_layer.risk.position_sizer import PositionSizer
from strategy_layer.statistics import HypothesisTester
from strategy_layer.strategies.templates import NoiseBandStrategy


def test_half_kelly_is_default_and_capped():
    assert PositionSizer().fractional_kelly == 0.5
    assert PositionSizer().kelly(0.6, 2.0) == pytest.approx(0.2)


def test_hypothesis_tester_and_noise_band():
    returns = pd.Series([0.01] * 30)
    result = HypothesisTester().sharpe_t_test(returns)
    assert result.p_value == 0.0
    dates = pd.date_range("2024-01-01", periods=25)
    data = pd.DataFrame({"Close": range(100, 125)}, index=dates)
    signals = NoiseBandStrategy(window=5).generate_signals(data)
    assert signals.index.equals(data.index)
