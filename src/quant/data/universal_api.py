from __future__ import annotations

from datetime import date, datetime
from quant.data.provider_bootstrap import build_fundamentals_service
from quant.data.metrics_engine import MetricsEngine


_service = build_fundamentals_service()
_engine = MetricsEngine(_service)


def get_metrics(
    symbol: str,
    fiscal_year: int,
    metrics: list[str],
    as_of_date: date | datetime | None = None,
):
    """
    Universal, provider-agnostic quant entrypoint.
    """
    return _engine.get_metrics(
        symbol=symbol,
        fiscal_year=fiscal_year,
        metrics=metrics,
        as_of_date=as_of_date,
    )