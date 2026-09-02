from quant.data.providers.sec_provider import SECFundamentalProvider
from quant.data.providers.global_provider import GlobalOpenBBProvider
from quant.data.providers.resolver import ProviderResolver
from quant.data.fundamentals_service import FundamentalsService
from quant.validation.filing_matcher import FilingFinancialMatcher
from quant.data.cache_store import FinancialValueCache

def build_fundamentals_service() -> FundamentalsService:
    sec = SECFundamentalProvider(
        symbol_to_cik={
            "AAPL": "0000320193",
            "MSFT": "0000789019",
        }
    )
    global_provider = GlobalOpenBBProvider()
    resolver = ProviderResolver(sec_provider=sec, global_provider=global_provider)
    matcher = FilingFinancialMatcher()
    cache = FinancialValueCache(".cache/fundamentals.sqlite")
    return FundamentalsService(
        resolver=resolver,
        matcher=matcher,
        cache=cache,
    )