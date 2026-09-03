from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from quant.data.models import FilingFact, FinancialValue
from quant.data.openbb_client import OpenBBClient
from .base import FundamentalProvider, ProviderMetadata, AvailabilityQuality


class GlobalOpenBBProvider(FundamentalProvider):
    """
    First global provider version:
    - uses OpenBB fundamentals
    - does NOT rely on SEC companyfacts
    - returns FilingFact-like records synthesized from provider rows
    """

    name = "global_openbb"

    def __init__(self):
        self.openbb = OpenBBClient(provider="global_openbb")

    def supports_symbol(self, symbol: str) -> bool:
        # fallback provider: supports everything not handled by SEC
        return True

    def get_statement(self, symbol: str, statement: str, limit: int = 10):
        return self.openbb.get_statement(symbol=symbol, statement=statement, limit=limit)

    def get_financial_value(
        self,
        dataframe: Any,
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
    ) -> FinancialValue:
        rows = dataframe[
            (dataframe["fiscal_year"] == fiscal_year)
            & (dataframe.get("fiscal_period", "FY") == fiscal_period)
        ]

        if rows.empty:
            raise ValueError(f"No data found for {symbol} FY{fiscal_year} {fiscal_period}.")

        # deterministic pick: latest filing/accepted first if available
        sort_cols = [c for c in ["accepted_date", "filing_date", "period_ending"] if c in rows.columns]
        if sort_cols:
            rows = rows.sort_values(sort_cols, ascending=False)

        row = rows.iloc[0]
        value_series = self.openbb.get_field(dataframe, field)
        value = float(value_series.loc[row.name])

        return FinancialValue(
            symbol=symbol.upper(),
            field=field,
            value=value,
            currency=row.get("reported_currency"),
            period_end=row["period_ending"],
            fiscal_year=row.get("fiscal_year"),
            fiscal_period=row.get("fiscal_period"),
            filing_date=row.get("filing_date"),
            accepted_date=_to_utc_aware_or_none(row.get("accepted_date")),
            provider=self.name,
        )

    def get_facts(self, symbol: str, concepts: list[str]) -> list[FilingFact]:
        # No SEC concepts globally. Return empty for now.
        # Next iteration: provider-specific concept mapping.
        return []

    def get_metadata(self, symbol: str) -> ProviderMetadata:
        return ProviderMetadata(
            provider=self.name,
            availability_quality=AvailabilityQuality.DATE_ONLY,
            country=None,
            exchange=None,
        )


def _to_utc_aware_or_none(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None