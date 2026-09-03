from __future__ import annotations

from datetime import date, datetime, timezone, time
from dataclasses import dataclass

from quant.data.models import FinancialValue, MatchResult
from quant.validation.filing_matcher import FilingFinancialMatcher
from quant.validation.concept_map import SEC_CONCEPTS
from quant.data.providers.resolver import ProviderResolver
from quant.data.cache_store import FinancialValueCache


@dataclass
class FundamentalQueryResult:
    financial_value: FinancialValue
    provider_name: str
    provider_reason: str
    match_result: MatchResult | None
    cache_hit: bool = False


class FundamentalsService:
    def __init__(
        self,
        resolver: ProviderResolver,
        matcher: FilingFinancialMatcher,
        cache: FinancialValueCache | None = None,
    ):
        self.resolver = resolver
        self.matcher = matcher
        self.cache = cache or FinancialValueCache()

    def get_value(
        self,
        symbol: str,
        field: str,
        fiscal_year: int,
        statement: str,
        as_of_date: date | datetime | None = None,
        fiscal_period: str = "FY",
        limit: int = 20,
        use_cache: bool = True,
    ) -> FundamentalQueryResult:
        resolved = self.resolver.resolve(symbol)
        provider = resolved.provider
        as_of_dt: datetime | None = None
        if as_of_date is not None:
            if isinstance(as_of_date, datetime):
                as_of_dt = as_of_date if as_of_date.tzinfo is not None else as_of_date.replace(tzinfo=timezone.utc)
            else:
                as_of_dt = datetime.combine(as_of_date, time.max, tzinfo=timezone.utc)

        # ---------- cache lookup ----------
        if use_cache:
            cached = self.cache.get(
                provider=provider.name,
                symbol=symbol,
                field=field,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                as_of_date=as_of_date,
            )
        if cached is not None:
            return FundamentalQueryResult(
                financial_value=cached,
                provider_name=provider.name,
                provider_reason=f"{resolved.reason} (cache)",
                match_result=None,
                cache_hit=True,
            )

        df = provider.get_statement(symbol=symbol, statement=statement, limit=limit)
        fv = provider.get_financial_value(
            dataframe=df,
            symbol=symbol,
            field=field,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
        )

        if as_of_dt is not None:
            if fv.accepted_date is not None:
                fv.available_at = fv.accepted_date if fv.accepted_date.tzinfo is not None else fv.accepted_date.replace(tzinfo=timezone.utc)
            elif fv.filing_date is not None:
                fv.available_at = datetime.combine(fv.filing_date, time.max, tzinfo=timezone.utc)
            else:
                raise ValueError(f"Provider '{provider.name}' did not supply availability timestamps for {symbol} FY{fiscal_year} {fiscal_period}; "f"cannot ensure PIT as of {as_of_date!r}.")
            if fv.available_at > as_of_dt:
                raise ValueError(f"Requested PIT value for {symbol} FY{fiscal_year} ({field}) not available as of {as_of_date!r}. "f"Value available at {fv.available_at.isoformat()}.")

        if use_cache:
            self.cache.put(fv)
            try:
                self.cache.put(fv, as_of_date=as_of_date)
            except TypeError:
                self.cache.put(fv)
        match_result = None

        if field in SEC_CONCEPTS:
            facts = provider.get_facts(symbol=symbol, concepts=SEC_CONCEPTS[field])
            if facts:
                match_result = self.matcher.match(
                    openbb_value=fv,
                    sec_facts=facts,
                    as_of_date=as_of_date,
                )

        return FundamentalQueryResult(
            financial_value=fv,
            provider_name=provider.name,
            provider_reason=resolved.reason,
            match_result=match_result,
            cache_hit=False,
        )