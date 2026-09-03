from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from quant.validation.filing_matcher import FilingFinancialMatcher, AvailabilityPolicy
from quant.data.models import FinancialValue, FilingFact
from quant.data.providers.sec_provider import SECFundamentalProvider

def make_fact(period_end, accession, filing_date=None, accepted_date=None, value=1_000.0):
    return FilingFact(
        concept="Assets",
        value=value,
        unit="USD",
        period_start=None,
        period_end=period_end,
        fiscal_year=None,
        fiscal_period="FY",
        filing_date=filing_date,
        accepted_date=accepted_date,
        form="10-K",
        accession_number=accession,
        cik="0000000000",
    )

def make_openbb_value(symbol="MSFT", field="total_assets", value=1000.0, period_end=None):
    return FinancialValue(
        symbol=symbol,
        field=field,
        value=value,
        currency="USD",
        period_end=period_end,
        fiscal_year=None,
        fiscal_period="FY",
        filing_date=None,
        accepted_date=None,
        provider="openbb",
    )

def test_matcher_filters_by_as_of_date():
    matcher = FilingFinancialMatcher()
    openbb_value = make_openbb_value(period_end=date(2017, 6, 30))

    # fact accepted after as_of -> filtered out
    fact_late = make_fact(period_end=date(2017, 6, 30), accession="A1", accepted_date=datetime(2017, 8, 2, tzinfo=timezone.utc))
    # fact accepted before as_of -> allowed
    fact_early = make_fact(period_end=date(2017, 6, 30), accession="A2", accepted_date=datetime(2017, 8, 1, tzinfo=timezone.utc))

    res_before = matcher.match(openbb_value, [fact_late, fact_early], as_of_date=datetime(2017, 8, 1, tzinfo=timezone.utc))
    # only fact_early should remain -> should select it (if values match)
    assert res_before.sec_fact is not None
    assert res_before.sec_fact.accession_number == "A2"

def test_sec_provider_pit_selection(monkeypatch):
    """
    Test SECFundamentalProvider.get_financial_value picks SEC fact that is
    available at or before as_of_date or raises when none available.
    """
    # Prepare a fake OpenBB client that returns a FinancialValue without dates
    fake_openbb = MagicMock()
    fv = make_openbb_value(period_end=date(2008, 12, 31), value=2175052000000.0)
    fake_openbb.get_financial_value.return_value = fv

    # Prepare a fake SEC client that returns facts
    fake_sec = MagicMock()
    fact_accepted_2010 = make_fact(period_end=date(2008, 12, 31), accession="ACC1", accepted_date=datetime(2010, 2, 24, tzinfo=timezone.utc))
    fake_sec.get_facts.return_value = [fact_accepted_2010]

    provider = SECFundamentalProvider(symbol_to_cik={"JPM": "0000019617"})
    # inject fakes
    provider.openbb = fake_openbb
    provider.sec = fake_sec

    # as_of before acceptance should raise
    with pytest.raises(ValueError):
        provider.get_financial_value(
            dataframe=None,
            symbol="JPM",
            field="total_assets",
            fiscal_year=2008,
            fiscal_period="FY",
            as_of_date=date(2009, 12, 31),
        )

    # as_of after acceptance should return a FinancialValue and include accepted_date from the SEC fact
    res = provider.get_financial_value(
        dataframe=None,
        symbol="JPM",
        field="total_assets",
        fiscal_year=2008,
        fiscal_period="FY",
        as_of_date=datetime(2018, 1, 1, tzinfo=timezone.utc),
    )
    assert res.accepted_date is not None