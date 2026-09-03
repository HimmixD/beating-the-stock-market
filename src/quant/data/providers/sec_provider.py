from __future__ import annotations

import os
from typing import Optional
from datetime import date, datetime, timezone

from quant.data.models import FilingFact, FinancialValue
from quant.data.openbb_client import OpenBBClient
from quant.data.sec_client import SECClient
from quant.validation.concept_map import SEC_CONCEPTS
from .base import FundamentalProvider, ProviderMetadata, AvailabilityQuality
from quant.data.symbol_registry import SymbolRegistry



def _to_utc_aware_or_none(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None

class SECFundamentalProvider(FundamentalProvider):
    name = "sec"

    def __init__(self, symbol_to_cik: Optional[dict[str, str]] = None):
        self.openbb = OpenBBClient(provider="sec")
        self.sec = SECClient()
        self.registry = SymbolRegistry(".cache/fundamentals.sqlite")
        self.symbol_to_cik = {k.upper(): v for k, v in (symbol_to_cik or {}).items()}

        # one-time auto bootstrap for SEC map
        try:
            ua = os.getenv("SEC_USER_AGENT")
            if ua:
                self.registry.refresh_sec_ticker_map(user_agent=ua)
        except Exception:
            pass

    def supports_symbol(self, symbol: str) -> bool:
        s = symbol.upper()
        if s in self.symbol_to_cik:
            return True
        return self.registry.get_cik(s) is not None

    def _get_cik(self, symbol: str) -> str:
        s = symbol.upper()
        if s in self.symbol_to_cik:
            return self.symbol_to_cik[s]
        cik = self.registry.get_cik(s)
        if cik:
            return cik
        raise ValueError(f"No CIK mapping found for symbol '{symbol}'.")

    def get_statement(self, symbol: str, statement: str, limit: int = 10):
        return self.openbb.get_statement(symbol=symbol, statement=statement, limit=limit)

    def get_financial_value(
        self,
        dataframe,
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
        as_of_date: date | datetime | None = None,
    ) -> FinancialValue:
        # Get the raw OpenBB value first (may or may not have filing/accepted metadata)
        fv = self.openbb.get_financial_value(
            dataframe=dataframe,
            symbol=symbol,
            field=field,
            fiscal_year=fiscal_year,
        )
        # Normalize as_of_date -> datetime end-of-day UTC
        as_of_dt = None
        if as_of_date is not None:
            if isinstance(as_of_date, datetime):
                as_of_dt = as_of_date if as_of_date.tzinfo is not None else as_of_date.replace(tzinfo=timezone.utc)
            else:
                as_of_dt = datetime.combine(as_of_date, datetime.max.time(), tzinfo=timezone.utc)

        # Fetch SEC facts for the field's mapped concepts so we can find authoritative PIT timestamps.
        concepts = SEC_CONCEPTS.get(field, [])
        sec_facts: list[FilingFact] = []
        if concepts:
            sec_facts = self.sec.get_facts(
                cik=self._get_cik(symbol),
                concepts=concepts,
            )

        # Find candidate SEC facts matching the reporting period_end (and fiscal_period if available)
        candidates = [
            fact
            for fact in sec_facts
            if fact.period_end == fv.period_end
            and (fv.fiscal_period is None or fact.fiscal_period == fv.fiscal_period)
        ]

        def _available_at(fact: FilingFact):
            if fact.accepted_date is not None:
                return fact.accepted_date
            if fact.filing_date is not None:
                return datetime.combine(fact.filing_date, datetime.max.time(), tzinfo=timezone.utc)
            return None

        selected_fact = None
        if candidates:
            if as_of_dt is None:
                # no PIT requested: pick the most recent accepted (or filing) timestamp
                candidates = sorted(candidates, key=lambda f: (_available_at(f) or datetime.min), reverse=True)
                selected_fact = candidates[0]
            else:
                # PIT requested: pick the candidate with the latest available_at <= as_of_dt
                valid = [f for f in candidates if (_available_at(f) is not None and _available_at(f) <= as_of_dt)]
                if valid:
                    valid = sorted(valid, key=lambda f: _available_at(f), reverse=True)
                    selected_fact = valid[0]
                else:
                    # No SEC fact was available as-of the requested date -> not PIT-available
                    raise ValueError(
                        f"No SEC filing for {symbol} {fv.period_end} was available by {as_of_date!r}; cannot return PIT value."
                    )

        # If we selected a SEC fact, update fv's dates from it (authoritative)
        if selected_fact:
            fv = FinancialValue(
                symbol=fv.symbol,
                field=fv.field,
                value=fv.value,
                currency=fv.currency,
                period_end=fv.period_end,
                fiscal_year=fv.fiscal_year,
                fiscal_period=fv.fiscal_period,
                filing_date=selected_fact.filing_date,
                accepted_date=_to_utc_aware_or_none(selected_fact.accepted_date) if selected_fact.accepted_date else None,
                provider=self.name,
            )

        # If no SEC fact at all, we fallback to the OpenBB-supplied dates (may be None).
        # The caller (FundamentalsService) will still enforce PIT if as_of_date was provided.
        return fv

    
    def get_facts(self, symbol: str, concepts: list[str]) -> list[FilingFact]:
        cik = self._get_cik(symbol)
        return self.sec.get_facts(cik=cik, concepts=concepts)

    def get_metadata(self, symbol: str) -> ProviderMetadata:
        return ProviderMetadata(
            provider=self.name,
            availability_quality=AvailabilityQuality.EXACT_TIMESTAMP,
            country="US",
            exchange=None,
        )
