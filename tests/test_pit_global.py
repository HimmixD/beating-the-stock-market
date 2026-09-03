import pytest
from datetime import date, datetime, timezone

import pandas as pd

from quant.data.providers.global_provider import GlobalOpenBBProvider

def make_row(period_ending, fiscal_year, filing_date=None, accepted_date=None, reported_currency="USD", val=1000.0):
    return {
        "period_ending": period_ending,
        "fiscal_year": fiscal_year,
        "fiscal_period": "FY",
        "filing_date": filing_date,
        "accepted_date": accepted_date,
        "reported_currency": reported_currency,
        "total_assets": val,
    }

def test_global_provider_pit_filtering():
    provider = GlobalOpenBBProvider()

    rows = [
        make_row(period_ending=date(2008, 12, 31), fiscal_year=2008, filing_date=date(2010, 2, 24), accepted_date=None, val=1.0),
        make_row(period_ending=date(2008, 12, 31), fiscal_year=2008, filing_date=date(2009, 1, 15), accepted_date=datetime(2009, 1, 20, tzinfo=timezone.utc), val=2.0),
    ]
    df = pd.DataFrame(rows)

    # as_of before the second row's accepted_date (2009-01-19) should only allow rows with available_at <= as_of
    with pytest.raises(ValueError):
        provider.get_financial_value(dataframe=df, symbol="FAKE", field="total_assets", fiscal_year=2008, as_of_date=date(2009, 1, 19))

    # as_of at/after accepted_date should succeed and pick the proper row (value 2.0)
    res = provider.get_financial_value(dataframe=df, symbol="FAKE", field="total_assets", fiscal_year=2008, as_of_date=datetime(2009, 1, 21, tzinfo=timezone.utc))
    assert res.value == 2.0