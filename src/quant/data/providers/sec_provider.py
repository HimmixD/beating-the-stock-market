from __future__ import annotations

import os
from typing import Optional
from datetime import date, datetime, timezone, time

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


def _as_of_to_utc(as_of_date: date | datetime | None) -> datetime | None:
    if as_of_date is None:
        return None
    if isinstance(as_of_date, datetime):
        return as_of_date if as_of_date.tzinfo is not None else as_of_date.replace(tzinfo=timezone.utc)
    return datetime.combine(as_of_date, time.max, tzinfo=timezone.utc)


class SECFundamentalProvider(FundamentalProvider):
    name = "sec"

    def __init__(self, symbol_to_cik: Optional[dict[str, str]] = None):
        self.openbb = OpenBBClient(provider="sec")  # optional cross-check only
        self.sec = SECClient()
        self.registry = SymbolRegistry(".cache/fundamentals.sqlite")
        self.symbol_to_cik = {k.upper(): v for k, v in (symbol_to_cik or {}).items()}

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
        # Kept for interface compatibility / possible cross-check path
        return self.openbb.get_statement(symbol=symbol, statement=statement, limit=limit)

    def _available_at(self, fact: FilingFact) -> datetime:
        if fact.accepted_date is not None:
            return fact.accepted_date if fact.accepted_date.tzinfo else fact.accepted_date.replace(tzinfo=timezone.utc)
        if fact.filing_date is not None:
            return datetime.combine(fact.filing_date, time.max, tzinfo=timezone.utc)
        return datetime.max.replace(tzinfo=timezone.utc)

    def _select_best_fact(
        self,
        facts: list[FilingFact],
        fiscal_year: int,
        fiscal_period: str,
        as_of_dt: datetime | None,
    ) -> FilingFact:
        cands = [f for f in facts if f.fiscal_year == fiscal_year and (f.fiscal_period == fiscal_period or f.fiscal_period is None)]

        if not cands:
            # fallback around FY labels
            cands = [f for f in facts if f.fiscal_year is None or abs(int(f.fiscal_year) - int(fiscal_year)) <= 1]

        if as_of_dt is not None:
            cands = [f for f in cands if self._available_at(f) <= as_of_dt]

        if not cands:
            raise ValueError("No SEC fact candidate available under PIT constraints.")

        preferred_forms = {"10-K": 0, "10-K/A": 1, "10-Q": 2, "10-Q/A": 3}

        cands = sorted(
            cands,
            key=lambda f: (
                preferred_forms.get((f.form or ""), 99),
                -self._available_at(f).timestamp(),
                f.accession_number or "",
            ),
        )
        return cands[0]

    def get_financial_value(
        self,
        dataframe,  # unused on SEC-first path
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
        as_of_date: date | datetime | None = None,
    ) -> FinancialValue:
        concepts = SEC_CONCEPTS.get(field, [])
        if not concepts:
            raise ValueError(f"No SEC concept mapping for field '{field}'.")

        cik = self._get_cik(symbol)
        facts = self.sec.get_facts(cik=cik, concepts=concepts)
        if not facts:
            raise ValueError(f"No SEC facts returned for {symbol} ({cik}) field={field}.")

        as_of_dt = _as_of_to_utc(as_of_date)
        best = self._select_best_fact(facts, fiscal_year=fiscal_year, fiscal_period=fiscal_period, as_of_dt=as_of_dt)

        return FinancialValue(
            symbol=symbol.upper(),
            field=field,
            value=float(best.value),
            currency="USD" if (best.unit or "").upper() == "USD" else best.unit,
            period_end=best.period_end,
            fiscal_year=best.fiscal_year if best.fiscal_year is not None else fiscal_year,
            fiscal_period=best.fiscal_period or fiscal_period,
            filing_date=best.filing_date,
            accepted_date=_to_utc_aware_or_none(best.accepted_date),
            provider=self.name,
            source="sec_fact",
            pit_status="authoritative",
            confidence=1.0,
            source_concept=best.concept,
            source_unit=best.unit,
            source_form=best.form,
            source_accession=best.accession_number,
            source_cik=best.cik,
        )

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