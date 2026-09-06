import pytest
from datetime import datetime, timezone, date

from quant.data.openbb_client import OpenBBClient
from quant.data.sec_client import SECClient
from quant.validation.concept_map import SEC_CONCEPTS
from quant.validation.filing_matcher import FilingFinancialMatcher


# ---------------------------------------------------------------------------
# Real-data metric cases
# ---------------------------------------------------------------------------

METRIC_CASES = [

    # -----------------------------------------------------------------------
    # AAPL FY2009
    # -----------------------------------------------------------------------

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "total_assets",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "total_liabilities",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "stockholders_equity",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "cash_and_cash_equivalents",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "operating_cash_flow",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2009,
        "field": "capital_expenditures",
    },

    # -----------------------------------------------------------------------
    # AAPL FY2015
    # -----------------------------------------------------------------------

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "total_assets",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "total_liabilities",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "stockholders_equity",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "cash_and_cash_equivalents",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "operating_cash_flow",
    },

    {
        "symbol": "AAPL",
        "cik": "0000320193",
        "fiscal_year": 2015,
        "field": "capital_expenditures",
    },

    # -----------------------------------------------------------------------
    # MSFT FY2017
    # -----------------------------------------------------------------------

    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "total_assets",
    },

    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "total_liabilities",
    },

    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "stockholders_equity",
    },

    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "cash_and_cash_equivalents",
    },

    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "operating_cash_flow",
    },

    {
        "symbol": "MSFT",
        "cik": "0000789019",
        "fiscal_year": 2017,
        "field": "capital_expenditures",
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
def test_real_filing_matches_additional_metric(case):

    openbb_client = OpenBBClient()
    sec_client = SECClient()
    matcher = FilingFinancialMatcher()

    symbol = case["symbol"]
    cik = case["cik"]
    fiscal_year = case["fiscal_year"]
    field = case["field"]

    # -----------------------------------------------------------------------
    # 1. OpenBB PIT data
    # -----------------------------------------------------------------------

    statement = _statement_for_field(field)

    dataframe = openbb_client.get_statement(
        symbol=symbol,
        statement=statement,
        limit=20,
    )

    openbb_value = openbb_client.get_financial_value(
        dataframe=dataframe,
        symbol=symbol,
        field=field,
        fiscal_year=fiscal_year,
    )

    # -----------------------------------------------------------------------
    # 2. SEC Company Facts
    # -----------------------------------------------------------------------

    assert field in SEC_CONCEPTS, (
        f"No SEC concept mapping exists for field '{field}'."
    )

    sec_facts = sec_client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    assert sec_facts, (
        f"No SEC facts found for "
        f"{symbol} FY{fiscal_year} {field}."
    )

    # -----------------------------------------------------------------------
    # 3. Matcher
    # -----------------------------------------------------------------------

    result = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
    )

    # -----------------------------------------------------------------------
    # 4. Diagnostics
    # -----------------------------------------------------------------------

    print("\n" + "=" * 90)
    print(
        f"{symbol} FY{fiscal_year} {field}"
    )
    print("=" * 90)

    print(
        f"OpenBB value:        "
        f"{openbb_value.value:,.2f}"
    )

    print(
        f"OpenBB period_end:   "
        f"{openbb_value.period_end}"
    )

    print(
        f"OpenBB fiscal_year:  "
        f"{openbb_value.fiscal_year}"
    )

    print(
        f"OpenBB fiscal_period: "
        f"{openbb_value.fiscal_period}"
    )

    print(
        f"OpenBB filing_date:  "
        f"{openbb_value.filing_date}"
    )

    print(
        f"SEC facts:           "
        f"{len(sec_facts)}"
    )

    print(
        f"Matched:             "
        f"{result.matched}"
    )

    print(
        f"Confidence:          "
        f"{result.confidence}"
    )

    print(
        f"Reason:              "
        f"{result.reason}"
    )

    if result.sec_fact:

        print(
            f"SEC concept:         "
            f"{result.sec_fact.concept}"
        )

        print(
            f"SEC value:           "
            f"{result.sec_fact.value:,.2f}"
        )

        print(
            f"SEC period_end:      "
            f"{result.sec_fact.period_end}"
        )

        print(
            f"SEC fiscal_year:     "
            f"{result.sec_fact.fiscal_year}"
        )

        print(
            f"SEC fiscal_period:   "
            f"{result.sec_fact.fiscal_period}"
        )

        print(
            f"SEC filing_date:     "
            f"{result.sec_fact.filing_date}"
        )

        print(
            f"SEC accepted_date:   "
            f"{result.sec_fact.accepted_date}"
        )

        print(
            f"SEC form:            "
            f"{result.sec_fact.form}"
        )

        print(
            f"SEC accession:       "
            f"{result.sec_fact.accession_number}"
        )

    # -----------------------------------------------------------------------
    # 5. Assertions
    # -----------------------------------------------------------------------

    assert openbb_value.fiscal_year == fiscal_year

    assert result.matched is True, (
        f"\nMatcher failed for "
        f"{symbol} FY{fiscal_year} {field}\n"
        f"OpenBB value: {openbb_value.value}\n"
        f"OpenBB period_end: {openbb_value.period_end}\n"
        f"Reason: {result.reason}"
    )

    assert result.sec_fact is not None

    assert result.sec_fact.period_end == (
        openbb_value.period_end
    )

    assert result.sec_fact.fiscal_period == (
        openbb_value.fiscal_period
    )

    assert result.value_difference == pytest.approx(0.0)


def _statement_for_field(field: str) -> str:

    income_fields = {
        "revenue",
        "gross_profit",
        "operating_income",
        "net_income",
    }

    balance_fields = {
        "total_assets",
        "total_liabilities",
        "stockholders_equity",
        "cash_and_cash_equivalents",
    }

    cash_fields = {
        "operating_cash_flow",
        "capital_expenditures",
    }

    if field in income_fields:
        return "income"

    if field in balance_fields:
        return "balance"

    if field in cash_fields:
        return "cash"

    raise ValueError(
        f"No statement mapping exists for field '{field}'."
    )

@pytest.mark.integration
@pytest.mark.parametrize(
    "symbol,fiscal_year",
    [
        ("AAPL", 2009),
        ("AAPL", 2015),
        ("MSFT", 2017),
    ],
)
def test_debug_cash_statement(symbol, fiscal_year):

    client = OpenBBClient()

    dataframe = client.get_statement(
        symbol=symbol,
        statement="cash",
        limit=20,
    )

    print("\n" + "=" * 100)
    print(f"{symbol} CASH STATEMENT")
    print("=" * 100)

    print(
        dataframe[
            [
                "period_ending",
                "fiscal_period",
                "fiscal_year",
                "reported_currency",
                "net_cash_from_operating_activities",
                "purchase_of_plant_property_and_equipment",
                "cash_at_end_of_period",
            ]
        ].to_string(index=False)
    )

    print("\nRequested fiscal year:", fiscal_year)

    rows = dataframe[
        dataframe["fiscal_year"] == fiscal_year
    ]

    print("\nMatching rows:")
    print(rows.to_string(index=False))

    assert not rows.empty

@pytest.mark.integration
def test_debug_balance_columns():

    client = OpenBBClient()

    dataframe = client.get_statement(
        symbol="AAPL",
        statement="balance",
        limit=20,
    )

    print("\n" + "=" * 100)
    print("BALANCE SHEET COLUMNS")
    print("=" * 100)

    print(dataframe.columns.tolist())

    print("\nRelevant rows:")

    columns = [
        column
        for column in [
            "period_ending",
            "fiscal_period",
            "fiscal_year",
            "total_assets",
            "total_liabilities",
            "stockholders_equity",
            "total_stockholders_equity",
            "cash_and_cash_equivalents",
            "cash_and_short_term_investments",
        ]
        if column in dataframe.columns
    ]

    print(
        dataframe[columns].head(10).to_string(index=False)
    )

@pytest.mark.integration
def test_debug_sec_operating_cash_flow():

    client = SECClient()

    facts = client.get_facts(
        cik="0000320193",
        concepts=SEC_CONCEPTS["operating_cash_flow"],
    )

    print("\n" + "=" * 100)
    print("AAPL SEC OPERATING CASH FLOW FACTS FOR 2015-09-26")
    print("=" * 100)

    matching = [
        fact
        for fact in facts
        if fact.period_end == date(2015, 9, 26)
    ]

    matching.sort(
        key=lambda fact: (
            fact.accepted_date or datetime.min
        )
    )

    for fact in matching:

        print(
            f"concept={fact.concept} | "
            f"period_end={fact.period_end} | "
            f"fy={fact.fiscal_year} | "
            f"fp={fact.fiscal_period} | "
            f"value={fact.value:,.0f} | "
            f"filed={fact.filing_date} | "
            f"accepted={fact.accepted_date} | "
            f"form={fact.form} | "
            f"accn={fact.accession_number}"
        )

    assert matching

@pytest.mark.integration
@pytest.mark.parametrize(
    "symbol,cik,fiscal_year,field",
    [
        ("AAPL", "0000320193", 2009, "operating_cash_flow"),
        ("AAPL", "0000320193", 2015, "operating_cash_flow"),
        ("MSFT", "0000789019", 2017, "operating_cash_flow"),
    ],
)
def test_debug_sec_fiscal_year_behavior(
    symbol,
    cik,
    fiscal_year,
    field,
):

    client = SECClient()

    facts = client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    print("\n" + "=" * 100)
    print(
        f"{symbol} FY{fiscal_year} SEC FACTS"
    )
    print("=" * 100)

    for fact in facts:

        if fact.period_end.year in {
            fiscal_year - 1,
            fiscal_year,
            fiscal_year + 1,
        }:

            print(
                f"period_end={fact.period_end} | "
                f"fy={fact.fiscal_year} | "
                f"fp={fact.fiscal_period} | "
                f"value={fact.value:,.0f} | "
                f"filed={fact.filing_date} | "
                f"accepted={fact.accepted_date} | "
                f"form={fact.form} | "
                f"accn={fact.accession_number}"
            )

    assert facts