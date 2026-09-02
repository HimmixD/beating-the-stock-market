from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

from quant.data.models import FinancialValue, FilingFact


class AvailabilityQuality(str, Enum):
    EXACT_TIMESTAMP = "exact_timestamp"
    DATE_ONLY = "date_only"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderMetadata:
    provider: str
    availability_quality: AvailabilityQuality
    country: Optional[str] = None
    exchange: Optional[str] = None


class FundamentalProvider(ABC):
    name: str

    @abstractmethod
    def supports_symbol(self, symbol: str) -> bool:
        ...

    @abstractmethod
    def get_statement(
        self,
        symbol: str,
        statement: str,
        limit: int = 10,
    ) -> Any:
        ...

    @abstractmethod
    def get_financial_value(
        self,
        dataframe: Any,
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
    ) -> FinancialValue:
        ...

    @abstractmethod
    def get_facts(
        self,
        symbol: str,
        concepts: list[str],
    ) -> list[FilingFact]:
        ...

    @abstractmethod
    def get_metadata(self, symbol: str) -> ProviderMetadata:
        ...