from dataclasses import dataclass
from datetime import date, datetime

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

        # ---------- cache lookup ----------
        if use_cache:
            cached = self.cache.get(
                provider=provider.name,
                symbol=symbol,
                field=field,
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
            )
            if cached is not None:
                return FundamentalQueryResult(
                    financial_value=cached,
                    provider_name=provider.name,
                    provider_reason=f"{resolved.reason} (cache)",
                    match_result=None,
                    cache_hit=True,
                )

        # ---------- provider fetch ----------
        df = provider.get_statement(
            symbol=symbol,
            statement=statement,
            limit=limit,
        )

        fv = provider.get_financial_value(
            dataframe=df,
            symbol=symbol,
            field=field,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
        )

        # ---------- cache store ----------
        if use_cache:
            self.cache.put(fv)

        # ---------- optional SEC-style matching ----------
        match_result = None
        if field in SEC_CONCEPTS:
            facts = provider.get_facts(
                symbol=symbol,
                concepts=SEC_CONCEPTS[field],
            )
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