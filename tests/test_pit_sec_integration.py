import pytest
from datetime import date, datetime, timezone

from quant.data.provider_bootstrap import build_fundamentals_service

@pytest.mark.integration
def test_sec_pit_before_acceptance_raises():
    """
    Ensure that requesting a PIT value before the SEC filing acceptance raises a ValueError.

    Requires network access and SEC_USER_AGENT env var.
    """
    svc = build_fundamentals_service()

    # MSFT FY2017 10-K acceptance recorded as 2017-08-02; asking for 2017-08-01 should fail.
    with pytest.raises(ValueError):
        svc.get_value("MSFT", "revenue", 2017, "income", as_of_date=date(2017, 8, 1))

@pytest.mark.integration
def test_sec_pit_at_or_after_acceptance_returns_value_and_match():
    """
    Ensure that requesting a PIT value at/after SEC acceptance returns a FinancialValue
    and that matching against SEC facts succeeds for a mapped field.
    """
    svc = build_fundamentals_service()

    # Use a timestamp after the real acceptance (2017-08-02).
    as_of = datetime(2017, 8, 3, tzinfo=timezone.utc)
    result = svc.get_value("MSFT", "revenue", 2017, "income", as_of_date=as_of)

    assert result is not None
    assert result.financial_value is not None
    assert result.match_result is not None
    assert result.match_result.matched is True

@pytest.mark.integration
def test_non_pit_mode_returns_value_without_as_of():
    """
    When no as_of_date is supplied (non-PIT mode), the service should return the latest
    available FinancialValue without raising.
    """
    svc = build_fundamentals_service()

    result = svc.get_value("MSFT", "revenue", 2017, "income", as_of_date=None)

    assert result is not None
    assert result.financial_value is not None