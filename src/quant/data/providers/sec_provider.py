from __future__ import annotations

from typing import Optional

from quant.data.models import FilingFact, FinancialValue
from quant.data.openbb_client import OpenBBClient
from quant.data.sec_client import SECClient
from quant.validation.concept_map import SEC_CONCEPTS
from .base import FundamentalProvider, ProviderMetadata, AvailabilityQuality


class SECFundamentalProvider(FundamentalProvider):
    name = "sec"

    def __init__(self, symbol_to_cik: Optional[dict[str, str]] = None):
        self.openbb = OpenBBClient()
        self.sec = SECClient()
        self.symbol_to_cik = {k.upper(): v for k, v in (symbol_to_cik or {}).items()}

    def supports_symbol(self, symbol: str) -> bool:
        # simple first version: US-style ticker (no suffix) + has CIK mapping
        s = symbol.upper()
        return s in self.symbol_to_cik

    def get_statement(self, symbol: str, statement: str, limit: int = 10):
        return self.openbb.get_statement(symbol=symbol, statement=statement, limit=limit)

    def get_financial_value(
        self,
        dataframe,
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
    ) -> FinancialValue:
        # you can later harden this in OpenBBClient with deterministic row selection
        value = self.openbb.get_financial_value(
            dataframe=dataframe,
            symbol=symbol,
            field=field,
            fiscal_year=fiscal_year,
        )
        return value

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

    def _get_cik(self, symbol: str) -> str:
        s = symbol.upper()
        if s not in self.symbol_to_cik:
            raise ValueError(
                f"No CIK mapping configured for symbol '{symbol}'. "
                "Add it to symbol_to_cik for SEC matching."
            )
        return self.symbol_to_cik[s]