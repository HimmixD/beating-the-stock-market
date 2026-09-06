from unittest.mock import Mock

import requests

import pandas as pd

from quant.data.openbb_client import OpenBBClient

from quant.data.request_utils import retry_call


def test_retry_call_recovers_after_temporary_failure():

    function = Mock(
        side_effect=[
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            "success",
        ]
    )

    result = retry_call(
        function,
        attempts=3,
        initial_delay=0,
    )

    assert result == "success"

    assert function.call_count == 3


def test_retry_call_raises_after_all_attempts_fail():

    function = Mock(
        side_effect=requests.exceptions.Timeout()
    )

    try:

        retry_call(
            function,
            attempts=3,
            initial_delay=0,
        )

    except requests.exceptions.Timeout:
        pass

    else:
        raise AssertionError(
            "Expected Timeout after all retry attempts."
        )

    assert function.call_count == 3

def test_openbb_statement_cache():
    client = OpenBBClient()

    fake_dataframe = pd.DataFrame(
        {
            "fiscal_year": [2025],
            "period_ending": [pd.Timestamp("2025-12-31").date()],
            "fiscal_period": ["FY"],
            "total_revenue": [100.0],
        }
    )

    client._statement_cache[("sec", "AAPL", "income", 10, "annual", True)] = fake_dataframe.copy()

    result_1 = client.get_statement(symbol="AAPL", statement="income", limit=10)
    result_2 = client.get_statement(symbol="AAPL", statement="income", limit=10)

    assert result_1.equals(fake_dataframe)
    assert result_2.equals(fake_dataframe)
    assert client._statement_cache[("sec", "AAPL", "income", 10, "annual", True)].equals(fake_dataframe)


def test_sec_company_facts_cache():

    from quant.data.sec_client import SECClient

    client = SECClient()

    fake_data = {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {}
            }
        }
    }

    client._company_facts["0000320193"] = fake_data

    result_1 = client.get_company_facts(
        "0000320193"
    )

    result_2 = client.get_company_facts(
        "0000320193"
    )

    assert result_1 == fake_data
    assert result_2 == fake_data

    assert result_1 is result_2