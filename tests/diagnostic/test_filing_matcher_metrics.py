import pytest

from datetime import datetime, timezone

from quant.data.openbb_client import OpenBBClient
from quant.data.sec_client import SECClient
from quant.validation.concept_map import SEC_CONCEPTS
from quant.validation.filing_matcher import FilingFinancialMatcher


# ---------------------------------------------------------------------------
# Real-data metric cases
# ---------------------------------------------------------------------------
#
# We deliberately use the same companies / fiscal years that we already
# validated for Revenue.
#
# The test does NOT hard-code a particular SEC concept. Instead, the concept
# must come from SEC_CONCEPTS[field], exactly like the production matcher.
#
# This allows the test to answer the important question:
#
#     "Can the complete OpenBB PIT -> SEC -> Matcher pipeline resolve
#      different financial metrics correctly?"
#
# ---------------------------------------------------------------------------

METRIC_CASES = [
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "revenue",
        "as_of_date": datetime(
            2009, 10, 28,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "net_income",
        "as_of_date": datetime(
            2009, 10, 28,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "operating_income",
        "as_of_date": datetime(
            2009, 10, 28,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "gross_profit",
        "as_of_date": datetime(
            2009, 10, 28,
            tzinfo=timezone.utc,
        ),
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "revenue",
        "as_of_date": datetime(
            2015, 10, 29,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "net_income",
        "as_of_date": datetime(
            2015, 10, 29,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "operating_income",
        "as_of_date": datetime(
            2015, 10, 29,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "gross_profit",
        "as_of_date": datetime(
            2015, 10, 29,
            tzinfo=timezone.utc,
        ),
    },

    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "revenue",
        "as_of_date": datetime(
            2017, 8, 3,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "net_income",
        "as_of_date": datetime(
            2017, 8, 3,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "operating_income",
        "as_of_date": datetime(
            2017, 8, 3,
            tzinfo=timezone.utc,
        ),
    },
    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "gross_profit",
        "as_of_date": datetime(
            2017, 8, 3,
            tzinfo=timezone.utc,
        ),
    },
]


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    METRIC_CASES,
    ids=lambda case: (
        f"{case['symbol']}_"
        f"FY{case['fiscal_year']}_"
        f"{case['field']}"
    ),
)
def test_real_filing_matches_metric(case):
    """
    Validate the complete real-data pipeline for multiple financial metrics:

        OpenBB PIT
            ↓
        SEC Company Facts
            ↓
        FilingFinancialMatcher
            ↓
        PIT-correct SEC fact
    """

    openbb_client = OpenBBClient()
    sec_client = SECClient()
    matcher = FilingFinancialMatcher()

    symbol = case["symbol"]
    cik = case["cik"]
    fiscal_year = case["fiscal_year"]
    field = case["field"]
    as_of_date = case["as_of_date"]

    # ------------------------------------------------------------------
    # 1. Verify that the metric is actually mapped
    # ------------------------------------------------------------------

    assert field in SEC_CONCEPTS, (
        f"No SEC concept mapping exists for field '{field}'."
    )

    assert SEC_CONCEPTS[field], (
        f"SEC concept mapping for '{field}' is empty."
    )

    # ------------------------------------------------------------------
    # 2. OpenBB PIT data
    # ------------------------------------------------------------------

    dataframe = openbb_client.get_statement(
        symbol=symbol,
        statement="income",
        limit=20,
    )

    openbb_value = openbb_client.get_financial_value(
        dataframe=dataframe,
        symbol=symbol,
        field=field,
        fiscal_year=fiscal_year,
    )

    assert openbb_value is not None

    assert openbb_value.fiscal_year == fiscal_year

    # ------------------------------------------------------------------
    # 3. SEC Company Facts
    # ------------------------------------------------------------------

    sec_facts = sec_client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    assert sec_facts, (
        f"No SEC facts found for "
        f"{symbol} / {field}."
    )

    # ------------------------------------------------------------------
    # 4. Matcher
    # ------------------------------------------------------------------

    result = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=as_of_date,
    )

    # ------------------------------------------------------------------
    # 5. Diagnostics
    # ------------------------------------------------------------------

    print("\n" + "=" * 90)
    print(
        f"{symbol} FY{fiscal_year} {field}"
    )
    print("=" * 90)

    print("\nOpenBB:")
    print(f"  value:         {openbb_value.value}")
    print(f"  period_end:    {openbb_value.period_end}")
    print(f"  fiscal_year:   {openbb_value.fiscal_year}")
    print(f"  fiscal_period: {openbb_value.fiscal_period}")
    print(f"  filing_date:   {openbb_value.filing_date}")

    print("\nSEC concepts:")
    for concept in SEC_CONCEPTS[field]:
        print(f"  {concept}")

    print("\nMatcher:")
    print(f"  matched:       {result.matched}")
    print(f"  confidence:    {result.confidence}")
    print(f"  reason:        {result.reason}")

    if result.sec_fact:
        print("\nSelected SEC fact:")
        print(f"  concept:       {result.sec_fact.concept}")
        print(f"  value:         {result.sec_fact.value}")
        print(f"  period_end:    {result.sec_fact.period_end}")
        print(f"  fiscal_year:   {result.sec_fact.fiscal_year}")
        print(f"  fiscal_period: {result.sec_fact.fiscal_period}")
        print(f"  form:          {result.sec_fact.form}")
        print(f"  filing_date:   {result.sec_fact.filing_date}")
        print(f"  accepted_date: {result.sec_fact.accepted_date}")
        print(
            f"  accession:     "
            f"{result.sec_fact.accession_number}"
        )

    # ------------------------------------------------------------------
    # 6. Assertions
    # ------------------------------------------------------------------

    assert result.matched is True, (
        f"\nMatcher failed for "
        f"{symbol} FY{fiscal_year} {field}\n"
        f"OpenBB value: {openbb_value.value}\n"
        f"OpenBB period_end: {openbb_value.period_end}\n"
        f"OpenBB fiscal_period: {openbb_value.fiscal_period}\n"
        f"Reason: {result.reason}"
    )

    assert result.sec_fact is not None

    assert result.sec_fact.period_end == (
        openbb_value.period_end
    )

    assert result.sec_fact.fiscal_year == (
        openbb_value.fiscal_year
    )

    assert result.sec_fact.value == pytest.approx(
        openbb_value.value,
        rel=matcher.relative_tolerance,
        abs=matcher.value_tolerance,
    )