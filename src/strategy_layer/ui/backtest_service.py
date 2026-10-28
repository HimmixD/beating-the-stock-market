"""UI-independent orchestration for daily backtests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from pit_layer.clients.price_client import PriceClient
from strategy_layer.backtesting.engine import BacktestEngine, BacktestResult
from strategy_layer.strategies.templates import (
    NoiseBandStrategy,
    OvernightEffectStrategy,
    StatArbStrategy,
)


@dataclass(frozen=True)
class StrategyDefinition:
    key: str
    label: str
    description: str
    factory: Callable[..., object]


STRATEGIES = (
    StrategyDefinition(
        "noise_band",
        "Noise Bands",
        "Daily Bollinger-Band breakout template.",
        NoiseBandStrategy,
    ),
    StrategyDefinition(
        "overnight",
        "Overnight Effect",
        "Long exposure template for close-to-close prototyping.",
        OvernightEffectStrategy,
    ),
    StrategyDefinition(
        "stat_arb",
        "Statistical Arbitrage",
        "Pair mean-reversion using a rolling spread z-score.",
        StatArbStrategy,
    ),
)


@dataclass(frozen=True)
class BacktestRun:
    ticker: str
    strategy: StrategyDefinition
    prices: pd.DataFrame
    result: BacktestResult
    signals: pd.DataFrame


class BacktestService:
    def __init__(self, price_client: PriceClient | None = None):
        self.price_client = price_client or PriceClient()

    def run(
        self,
        ticker: str,
        strategy_key: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        transaction_cost_bps: float,
        strategy_params: dict | None = None,
    ) -> BacktestRun:
        definition = next((item for item in STRATEGIES if item.key == strategy_key), None)
        if definition is None:
            raise ValueError(f"Unbekannte Strategie: {strategy_key}")
        prices = self.price_client.fetch_historical_prices(
            ticker.upper(), start_date=start_date, end_date=end_date
        )
        if prices is None or prices.empty:
            raise ValueError(f"Keine Kursdaten für {ticker.upper()} im gewählten Zeitraum.")
        prices = prices.copy()
        prices.index = pd.to_datetime(prices.index).tz_localize(None)
        params = dict(strategy_params or {})
        if strategy_key == "stat_arb":
            other_ticker = str(params.pop("other_ticker", "")).upper()
            if not other_ticker:
                raise ValueError("Statistical Arbitrage benötigt einen zweiten Ticker.")
            other_prices = self.price_client.fetch_historical_prices(
                other_ticker, start_date=start_date, end_date=end_date
            )
            if other_prices is None or other_prices.empty:
                raise ValueError(f"Keine Pair-Daten für {other_ticker}.")
            other_close = other_prices["Close"].copy()
            other_close.index = pd.to_datetime(other_close.index).tz_localize(None)
            strategy = definition.factory(
                other_close=other_close,
                lookback=int(params.get("lookback", 60)),
                entry_z=float(params.get("entry_z", 2.0)),
            )
        else:
            strategy = definition.factory(**params)
        result = BacktestEngine(
            initial_capital=initial_capital,
            transaction_cost_bps=transaction_cost_bps,
        ).run(prices, strategy)
        signals = self._signal_breakdown(prices, strategy_key, params, result)
        return BacktestRun(ticker.upper(), definition, prices, result, signals)

    @staticmethod
    def _signal_breakdown(
        prices: pd.DataFrame,
        strategy_key: str,
        params: dict,
        result: BacktestResult,
    ) -> pd.DataFrame:
        breakdown = pd.DataFrame(index=prices.index)
        breakdown["close"] = prices["Close"]
        breakdown["position"] = result.positions
        if strategy_key == "noise_band":
            window = int(params.get("window", 20))
            num_std = float(params.get("num_std", 2.0))
            mean = prices["Close"].rolling(window).mean()
            band = prices["Close"].rolling(window).std() * num_std
            breakdown["middle_band"] = mean
            breakdown["upper_band"] = mean + band
            breakdown["lower_band"] = mean - band
            breakdown["signal_reason"] = result.positions.map(
                lambda value: "LONG breakout"
                if value > 0 else "SHORT breakout"
                if value < 0 else "FLAT / no breakout"
            )
        elif strategy_key == "stat_arb":
            breakdown["signal_reason"] = result.positions.map(
                lambda value: "LONG spread leg" if value > 0
                else "SHORT spread leg" if value < 0 else "FLAT / z-score inside band"
            )
        else:
            breakdown["signal_reason"] = result.positions.map(
                lambda value: "LONG exposure" if value > 0 else "FLAT"
            )
        return breakdown
