"""Daily, vectorized backtesting engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional

import pandas as pd


class Strategy(Protocol):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series: ...


@dataclass(frozen=True)
class BacktestResult:
    returns: pd.Series
    equity: pd.Series
    positions: pd.Series

    @property
    def total_return(self) -> float:
        return (
            float(self.equity.iloc[-1] / self.equity.iloc[0] - 1.0)
            if not self.equity.empty else 0.0
        )


class BacktestEngine:
    def __init__(self, initial_capital: float = 1.0, transaction_cost_bps: float = 0.0):
        if initial_capital <= 0 or transaction_cost_bps < 0:
            raise ValueError("initial_capital muss positiv und Kosten dürfen nicht negativ sein.")
        self.initial_capital = float(initial_capital)
        self.transaction_cost = transaction_cost_bps / 10_000

    def run(self, data: pd.DataFrame, strategy: Strategy,
            regime_filter: Optional[object] = None) -> BacktestResult:
        self._validate_data(data)
        signals = strategy.generate_signals(data.copy()).reindex(data.index).fillna(0.0)
        if regime_filter is not None:
            enabled = regime_filter.is_enabled(data)
            signals = signals.where(enabled.reindex(data.index).fillna(False), 0.0)
        positions = signals.clip(-1.0, 1.0).shift(1).fillna(0.0)
        asset_returns = data["Close"].pct_change().fillna(0.0)
        turnover = positions.diff().abs().fillna(positions.abs())
        returns = positions * asset_returns - turnover * self.transaction_cost
        equity = self.initial_capital * (1.0 + returns).cumprod()
        return BacktestResult(returns=returns, equity=equity, positions=positions)

    @staticmethod
    def _validate_data(data: pd.DataFrame) -> None:
        if not isinstance(data.index, pd.DatetimeIndex):
            raise TypeError("Backtestdaten benötigen einen DatetimeIndex.")
        if data.index.has_duplicates or not data.index.is_monotonic_increasing:
            raise ValueError("Backtestdaten müssen eindeutige, aufsteigende Daten enthalten.")
        if "Close" not in data.columns:
            raise ValueError("Backtestdaten benötigen eine Close-Spalte.")
