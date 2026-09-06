from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class FilingFact:
    concept: str
    value: float
    unit: str
    period_start: Optional[date]
    period_end: date
    fiscal_year: Optional[int]
    fiscal_period: Optional[str]
    filing_date: Optional[date]
    accepted_date: Optional[datetime]  # UTC aware when present
    form: Optional[str]
    accession_number: Optional[str]
    cik: Optional[str]


@dataclass(frozen=True)
class FinancialValue:
    symbol: str
    field: str
    value: float
    currency: Optional[str]
    period_end: date
    fiscal_year: Optional[int]
    fiscal_period: Optional[str]
    filing_date: Optional[date]
    accepted_date: Optional[datetime]  # UTC aware when present
    provider: str

    # NEW: PIT/provenance metadata
    source: str = "unknown"  # sec_fact | openbb
    pit_status: str = "unknown"  # authoritative | provider_claimed | not_pit_safe
    confidence: float = 0.0
    source_concept: Optional[str] = None
    source_unit: Optional[str] = None
    source_form: Optional[str] = None
    source_accession: Optional[str] = None
    source_cik: Optional[str] = None


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    openbb_value: FinancialValue
    sec_fact: Optional[FilingFact]
    value_difference: Optional[float]
    relative_difference: Optional[float]
    confidence: float
    reason: str