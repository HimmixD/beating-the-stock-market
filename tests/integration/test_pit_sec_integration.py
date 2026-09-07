import pytest
from datetime import date, datetime, timezone

from quant.data.provider_bootstrap import build_fundamentals_service


@pytest.mark.integration
def test_sec_pit_before_acceptance_raises():
    svc = build_fundamentals_service()
    with pytest.raises(ValueError):
        svc.get_value("MSFT", "revenue", 2017, as_of_date=date(2017, 8, 1))


@pytest.mark.integration
def test_sec_pit_at_or_after_acceptance_returns_authoritative_value():
    svc = build_fundamentals_service()
    as_of = datetime(2017, 8, 3, tzinfo=timezone.utc)
    result = svc.get_value("MSFT", "revenue", 2017, as_of_date=as_of)

    assert result is not None
    fv = result.financial_value
    assert fv is not None
    assert fv.provider == "sec"
    assert fv.source == "sec_fact"
    assert fv.pit_status == "authoritative"
    assert fv.accepted_date is not None
    assert fv.accepted_date <= as_of


@pytest.mark.integration
def test_non_pit_mode_returns_value_without_as_of():
    svc = build_fundamentals_service()
    result = svc.get_value("MSFT", "revenue", 2017, as_of_date=None)

    assert result is not None
    fv = result.financial_value
    assert fv is not None
    assert fv.provider == "sec"
    assert fv.source == "sec_fact"