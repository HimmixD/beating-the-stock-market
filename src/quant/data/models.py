from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class FilingFact:
    """
    Ein einzelner Financial Fact aus einem SEC Filing.
    """

    concept: str
    value: float

    unit: str

    period_start: Optional[date]
    period_end: date

    fiscal_year: Optional[int]
    fiscal_period: Optional[str]

    filing_date: Optional[date]
    accepted_date: Optional[datetime]

    form: Optional[str]
    accession_number: Optional[str]

    cik: Optional[str]


@dataclass(frozen=True)
class FinancialValue:
    """
    Ein standardisierter Financial Value aus OpenBB.
    """

    symbol: str
    field: str

    value: float
    currency: Optional[str]

    period_end: date
    fiscal_year: Optional[int]
    fiscal_period: Optional[str]

    filing_date: Optional[date]
    accepted_date: Optional[datetime]

    provider: str


@dataclass(frozen=True)
class MatchResult:
    """
    Ergebnis eines Matches zwischen OpenBB und SEC.
    """

    matched: bool

    openbb_value: FinancialValue
    sec_fact: Optional[FilingFact]

    value_difference: Optional[float]
    relative_difference: Optional[float]

    confidence: float

    reason: str