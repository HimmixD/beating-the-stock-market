from datetime import date, datetime, timezone

from quant.data.models import FilingFact, FinancialValue
from quant.validation.filing_matcher import FilingFinancialMatcher, AvailabilityPolicy


def _openbb():
    return FinancialValue(
        symbol="MSFT",
        field="revenue",
        value=100.0,
        currency="USD",
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2017, 8, 2),
        accepted_date=datetime(2017, 8, 2, 20, 0, tzinfo=timezone.utc),
        provider="sec",
    )


def _fact(accn: str, val: float, accepted: datetime | None, filed: date, unit="USD"):
    return FilingFact(
        concept="Revenues",
        value=val,
        unit=unit,
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=filed,
        accepted_date=accepted,
        form="10-K",
        accession_number=accn,
        cik="0000789019",
    )


def test_strict_policy_excludes_missing_accepted_date():
    matcher = FilingFinancialMatcher(
        availability_policy=AvailabilityPolicy.STRICT_ACCEPTED_ONLY
    )
    openbb = _openbb()
    fact = _fact("a", 100.0, None, date(2017, 8, 2))

    result = matcher.match(openbb, [fact], as_of_date=datetime(2017, 8, 3, tzinfo=timezone.utc))
    assert result.matched is False
    assert result.sec_fact is None


def test_latest_available_is_selected_in_pit_mode():
    matcher = FilingFinancialMatcher()
    openbb = _openbb()

    old = _fact("old", 90.0, datetime(2017, 8, 2, 16, 0, tzinfo=timezone.utc), date(2017, 8, 2))
    new = _fact("new", 100.0, datetime(2017, 8, 3, 16, 0, tzinfo=timezone.utc), date(2017, 8, 3))

    result = matcher.match(openbb, [old, new], as_of_date=datetime(2017, 8, 3, 16, 0, tzinfo=timezone.utc))
    assert result.sec_fact is not None
    assert result.sec_fact.accession_number == "new"


def test_unit_mismatch_is_rejected():
    matcher = FilingFinancialMatcher()
    openbb = _openbb()
    shares_fact = _fact("shares", 100.0, datetime(2017, 8, 2, 16, 0, tzinfo=timezone.utc), date(2017, 8, 2), unit="SHARES")

    result = matcher.match(openbb, [shares_fact], as_of_date=datetime(2017, 8, 3, tzinfo=timezone.utc))
    assert result.matched is False
    assert "Unit mismatch" in result.reason