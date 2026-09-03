from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from quant.data.models import FilingFact, FinancialValue
from quant.data.openbb_client import OpenBBClient
from .base import FundamentalProvider, ProviderMetadata, AvailabilityQuality


def _to_utc_aware_or_none(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


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
        as_of_date: date | datetime | None = None,
    ) -> FinancialValue:
        rows = dataframe[
            (dataframe["fiscal_year"] == fiscal_year)
            & (dataframe.get("fiscal_period", "FY") == fiscal_period)
        ]

        if rows.empty:
            raise ValueError(f"No data found for {symbol} FY{fiscal_year} {fiscal_period}.")

        # If caller requested point-in-time, filter rows that were available at as_of_date.
        as_of_dt = None
        if as_of_date is not None:
            if isinstance(as_of_date, datetime):
                as_of_dt = as_of_date if as_of_date.tzinfo is not None else as_of_date.replace(tzinfo=timezone.utc)
            else:
                as_of_dt = datetime.combine(as_of_date, datetime.max.time(), tzinfo=timezone.utc)

            def row_available_at(r):
                a = r.get("accepted_date")
                if a is not None:
                    # assume datetime-like in dataframe
                    return a if getattr(a, "tzinfo", None) is not None else a.replace(tzinfo=timezone.utc)
                f = r.get("filing_date")
                if f is not None:
                    return datetime.combine(f, datetime.max.time(), tzinfo=timezone.utc)
                return None

            avail_mask = []
            for _, r in rows.iterrows():
                av = row_available_at(r)
                avail_mask.append(av is not None and av <= as_of_dt)
            rows = rows.iloc[[i for i, ok in enumerate(avail_mask) if ok]]

            if rows.empty:
                raise ValueError(
                    f"No OpenBB row for {symbol} FY{fiscal_year} was available by {as_of_date!r}."
                )

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


