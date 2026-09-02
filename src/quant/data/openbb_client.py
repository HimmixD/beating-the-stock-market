from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any

import requests
from openbb import obb
from openbb_core.app.model.abstract.error import OpenBBError

from ..validation.concept_map import OPENBB_FIELDS
from .models import FinancialValue
from .request_utils import retry_call, OPENBB_RETRY_EXCEPTIONS


def _to_utc_or_none(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


class OpenBBClient:
    def __init__(self, provider: str = "sec"):
        self.provider = provider
        self._statement_cache: dict[tuple, Any] = {}

    def _retry_with_jitter(self, fn):
        last_exc = None
        for attempt in range(5):
            try:
                return fn()
            except OPENBB_RETRY_EXCEPTIONS as exc:
                last_exc = exc
                if attempt == 4:
                    raise
                sleep_s = (1.2 ** attempt) + random.uniform(0.1, 0.6)
                time.sleep(sleep_s)
        raise last_exc

    def get_statement(self, symbol: str, statement: str, limit: int = 10):
        symbol = symbol.upper()
        cache_key = (self.provider, symbol, statement, limit, "annual", True)
        if cache_key in self._statement_cache:
            return self._statement_cache[cache_key].copy()

        if statement == "income":
            def fetch():
                return obb.equity.fundamental.income(
                    symbol=symbol, provider=self.provider, period="annual", limit=limit, pit_mode=True
                ).to_df()
        elif statement == "balance":
            def fetch():
                return obb.equity.fundamental.balance(
                    symbol=symbol, provider=self.provider, period="annual", limit=limit, pit_mode=True
                ).to_df()
        elif statement == "cash":
            def fetch():
                return obb.equity.fundamental.cash(
                    symbol=symbol, provider=self.provider, period="annual", limit=limit, pit_mode=True
                ).to_df()
        else:
            raise ValueError(f"Unknown statement type: {statement}")

        # combine legacy retry wrapper + jittered outer retry
        df = self._retry_with_jitter(
            lambda: retry_call(fetch, attempts=3, initial_delay=0.8, exceptions=OPENBB_RETRY_EXCEPTIONS)
        )
        self._statement_cache[cache_key] = df.copy()
        return df

    def get_field(self, dataframe, field: str):
        possible_columns = OPENBB_FIELDS.get(field)
        if not possible_columns:
            raise ValueError(f"No OpenBB field mapping exists for '{field}'.")
        for column in possible_columns:
            if column in dataframe.columns:
                return dataframe[column]
        raise KeyError(
            f"None of the mapped OpenBB columns {possible_columns} exist.\n"
            f"Available columns:\n{list(dataframe.columns)}"
        )

    def get_financial_value(
        self,
        dataframe,
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
    ):
        rows = dataframe[dataframe["fiscal_year"] == fiscal_year].copy()

        if "fiscal_period" in rows.columns and fiscal_period:
            subset = rows[rows["fiscal_period"] == fiscal_period]
            if not subset.empty:
                rows = subset

        if rows.empty:
            raise ValueError(f"No OpenBB data found for {symbol} FY{fiscal_year} ({fiscal_period}).")

        sort_cols = [c for c in ["accepted_date", "filing_date", "period_ending"] if c in rows.columns]
        if sort_cols:
            rows = rows.sort_values(sort_cols, ascending=False)

        row = rows.iloc[0]
        value_series = self.get_field(dataframe, field)
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
            accepted_date=_to_utc_or_none(row.get("accepted_date")),
            provider=self.provider,
        )