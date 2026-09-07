from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from quant.data.models import FinancialValue


class AvailabilityQuality(str, Enum):
    EXACT_TIMESTAMP = "exact_timestamp"
    DATE_ONLY = "date_only"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderMetadata:
    provider: str
    availability_quality: AvailabilityQuality
    country: str | None = None
    exchange: str | None = None


class FundamentalProvider(ABC):
    name: str

    @abstractmethod
    def supports_symbol(self, symbol: str) -> bool:
        ...

    @abstractmethod
    def get_financial_value(
        self,
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
        as_of_date: date | datetime | None = None,
    ) -> FinancialValue:
        ...

    @abstractmethod
    def get_metadata(self, symbol: str) -> ProviderMetadata:
        ...