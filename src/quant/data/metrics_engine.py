from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from quant.data.fundamentals_service import FundamentalsService


@dataclass(frozen=True)
class MetricValue:
    symbol: str
    metric: str
    value: float | None
    currency: str | None
    fiscal_year: int
    provider: str
    note: str | None = None


STATEMENT_BY_FIELD = {
    "revenue": "income",
    "gross_profit": "income",
    "operating_income": "income",
    "net_income": "income",
    "total_assets": "balance",
    "total_liabilities": "balance",
    "stockholders_equity": "balance",
    "cash_and_cash_equivalents": "balance",
    "operating_cash_flow": "cash",
    "capital_expenditures": "cash",
}


class MetricsEngine:
    def __init__(self, service: FundamentalsService):
        self.service = service

    def get_metrics(
        self,
        symbol: str,
        fiscal_year: int,
        metrics: list[str],
        as_of_date: date | datetime | None = None,
    ) -> dict[str, MetricValue]:
        out: dict[str, MetricValue] = {}

        raw_cache = {}
        needed_raw = self._expand_dependencies(metrics)

        for field in needed_raw:
            statement = STATEMENT_BY_FIELD.get(field)
            if not statement:
                continue
            try:
                result = self.service.get_value(
                    symbol=symbol,
                    field=field,
                    fiscal_year=fiscal_year,
                    statement=statement,
                    as_of_date=as_of_date,
                )
                raw_cache[field] = result
                out[field] = MetricValue(
                    symbol=symbol,
                    metric=field,
                    value=result.financial_value.value,
                    currency=result.financial_value.currency,
                    fiscal_year=fiscal_year,
                    provider=result.provider_name,
                    note=result.provider_reason,
                )
            except Exception as exc:
                out[field] = MetricValue(
                    symbol=symbol,
                    metric=field,
                    value=None,
                    currency=None,
                    fiscal_year=fiscal_year,
                    provider="unknown",
                    note=f"missing raw metric: {exc}",
                )

        # Derived factors
        for m in metrics:
            if m in out:
                continue
            out[m] = self._derive_metric(symbol, fiscal_year, m, raw_cache)

        return out

    def _expand_dependencies(self, metrics: list[str]) -> list[str]:
        deps = set()
        for m in metrics:
            if m in STATEMENT_BY_FIELD:
                deps.add(m)
            elif m == "roic":
                deps |= {"operating_income", "total_assets", "cash_and_cash_equivalents", "total_liabilities"}
            elif m == "net_margin":
                deps |= {"net_income", "revenue"}
            elif m == "debt_to_equity":
                deps |= {"total_liabilities", "stockholders_equity"}
        return sorted(deps)

    def _derive_metric(self, symbol: str, fiscal_year: int, metric: str, raw_cache: dict):
        def g(name):
            x = raw_cache.get(name)
            return None if x is None else x.financial_value.value

        if metric == "roic":
            op = g("operating_income")
            assets = g("total_assets")
            cash = g("cash_and_cash_equivalents")
            liab = g("total_liabilities")
            if None in (op, assets, cash, liab):
                return MetricValue(symbol, "roic", None, None, fiscal_year, "derived", "missing inputs")
            invested_capital = (assets - (cash or 0.0)) - (liab or 0.0) * 0.0  # conservative placeholder
            if invested_capital == 0:
                return MetricValue(symbol, "roic", None, None, fiscal_year, "derived", "zero invested capital")
            return MetricValue(symbol, "roic", op / invested_capital, None, fiscal_year, "derived")

        if metric == "net_margin":
            ni = g("net_income")
            rev = g("revenue")
            if None in (ni, rev) or rev == 0:
                return MetricValue(symbol, "net_margin", None, None, fiscal_year, "derived", "missing or zero revenue")
            return MetricValue(symbol, "net_margin", ni / rev, None, fiscal_year, "derived")

        if metric == "debt_to_equity":
            debt = g("total_liabilities")
            eq = g("stockholders_equity")
            if None in (debt, eq) or eq == 0:
                return MetricValue(symbol, "debt_to_equity", None, None, fiscal_year, "derived", "missing or zero equity")
            return MetricValue(symbol, "debt_to_equity", debt / eq, None, fiscal_year, "derived")

        if metric == "pe":
            return MetricValue(symbol, "pe", None, None, fiscal_year, "derived", "needs price + EPS module")

        return MetricValue(symbol, metric, None, None, fiscal_year, "derived", "unsupported metric")