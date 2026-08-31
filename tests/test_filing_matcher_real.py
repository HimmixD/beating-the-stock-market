import pytest

from quant.data.openbb_client import OpenBBClient
from quant.data.sec_client import SECClient
from quant.validation.concept_map import SEC_CONCEPTS
from quant.validation.filing_matcher import FilingFinancialMatcher


# ---------------------------------------------------------------------------
# Real-data ground-truth cases
# ---------------------------------------------------------------------------

GROUND_TRUTH_CASES = [
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "revenue",
        "expected_accession": "0001193125-09-214859",
    },
    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "revenue",
        "expected_accession": "0001193125-15-356351",
    },
    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "revenue",
        "expected_accession": "0001564590-17-014900",
    },
]


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    GROUND_TRUTH_CASES,
    ids=lambda case: (
        f"{case['symbol']}_FY{case['fiscal_year']}_{case['field']}"
    ),
)
def test_real_filing_matches_ground_truth(case):
    """
    Test the FilingFinancialMatcher against real OpenBB PIT data
    and real SEC Company Facts.

    The expected accession number is the independently validated
    SEC filing containing the historical financial value.
    """

    openbb_client = OpenBBClient()
    sec_client = SECClient()
    matcher = FilingFinancialMatcher()

    symbol = case["symbol"]
    cik = case["cik"]
    fiscal_year = case["fiscal_year"]
    field = case["field"]

    # ---------------------------------------------------------------
    # 1. OpenBB PIT data
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # 2. SEC Company Facts
    # ---------------------------------------------------------------

    sec_facts = sec_client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    # ---------------------------------------------------------------
    # 3. Matcher
    # ---------------------------------------------------------------

    result = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
    )

    # ---------------------------------------------------------------
    # 4. Diagnostics
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        f"{symbol} FY{fiscal_year} {field}"
    )
    print("=" * 70)

    print(f"OpenBB value:        {openbb_value.value}")
    print(f"OpenBB period_end:   {openbb_value.period_end}")
    print(f"OpenBB fiscal_year:  {openbb_value.fiscal_year}")
    print(f"OpenBB fiscal_period: {openbb_value.fiscal_period}")
    print(f"OpenBB filing_date:  {openbb_value.filing_date}")

    print(f"SEC facts:           {len(sec_facts)}")

    print(f"Matched:             {result.matched}")
    print(f"Confidence:          {result.confidence}")
    print(f"Reason:              {result.reason}")

    if result.sec_fact:
        print(f"SEC concept:         {result.sec_fact.concept}")
        print(f"SEC value:           {result.sec_fact.value}")
        print(f"SEC period_end:      {result.sec_fact.period_end}")
        print(f"SEC fiscal_year:     {result.sec_fact.fiscal_year}")
        print(f"SEC fiscal_period:   {result.sec_fact.fiscal_period}")
        print(f"SEC filing_date:     {result.sec_fact.filing_date}")
        print(f"SEC form:             {result.sec_fact.form}")
        print(f"SEC accession:       {result.sec_fact.accession_number}")

    # ---------------------------------------------------------------
    # 5. Assertions
    # ---------------------------------------------------------------

    assert openbb_value.fiscal_year == fiscal_year

    assert result.matched is True, (
        f"\nMatcher failed for {symbol} FY{fiscal_year} {field}\n"
        f"OpenBB value: {openbb_value.value}\n"
        f"OpenBB period_end: {openbb_value.period_end}\n"
        f"Reason: {result.reason}"
    )

    assert result.sec_fact is not None

    assert result.sec_fact.accession_number == (
        case["expected_accession"]
    )

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


@pytest.mark.integration
def test_msft_revenue_candidates_2017():
    """
    Diagnostic test:
    Show all SEC revenue facts around MSFT FY2017.

    This does not change matcher behavior. It helps determine why
    OpenBB PIT reports FY2017 revenue of 89.95B while the matcher
    currently selects a 96.571B SEC fact.
    """

    symbol = "MSFT"
    cik = "0000789019"
    field = "revenue"

    openbb_client = OpenBBClient()
    sec_client = SECClient()

    # ---------------------------------------------------------------
    # OpenBB
    # ---------------------------------------------------------------

    dataframe = openbb_client.get_statement(
        symbol=symbol,
        statement="income",
        limit=20,
    )

    openbb_value = openbb_client.get_financial_value(
        dataframe=dataframe,
        symbol=symbol,
        field=field,
        fiscal_year=2017,
    )

    # ---------------------------------------------------------------
    # SEC
    # ---------------------------------------------------------------

    sec_facts = sec_client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    print("\n" + "=" * 100)
    print("MSFT FY2017 REVENUE DIAGNOSTIC")
    print("=" * 100)

    print("\nOpenBB:")
    print(f"  value:        {openbb_value.value}")
    print(f"  period_end:   {openbb_value.period_end}")
    print(f"  fiscal_year:  {openbb_value.fiscal_year}")
    print(f"  fiscal_period:{openbb_value.fiscal_period}")

    print("\nSEC candidates:")
    print("-" * 100)

    for fact in sec_facts:

        if fact.period_end != openbb_value.period_end:
            continue

        print(
            f"concept={fact.concept:55} "
            f"value={fact.value:15,.0f} "
            f"fy={str(fact.fiscal_year):4} "
            f"fp={str(fact.fiscal_period):4} "
            f"form={str(fact.form):6} "
            f"filed={str(fact.filing_date):10} "
            f"accn={fact.accession_number}"
        )

    assert openbb_value.value == pytest.approx(
        89_950_000_000,
        rel=0,
        abs=0,
    )
