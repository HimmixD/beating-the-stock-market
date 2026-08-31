from quant.data.sec_client import SECClient
from quant.data.openbb_client import OpenBBClient
from quant.data.models import FinancialValue

from quant.validation.filing_matcher import (
    FilingFinancialMatcher,
)


def main():

    symbol = "AAPL"
    cik = "0000320193"
    fiscal_year = 2009

    sec = SECClient()
    openbb = OpenBBClient()

    matcher = FilingFinancialMatcher(
        value_tolerance=0,
        relative_tolerance=1e-9,
    )

    # --------------------------------------------------
    # 1. OpenBB Daten laden
    # --------------------------------------------------

    income = openbb.get_statement(
        symbol=symbol,
        statement="income",
        limit=20,
    )

    print("OpenBB income statement:")
    print(income)
    print(income.columns.tolist())
    print(income.dtypes)
    print(income.iloc[0].to_dict())

    # --------------------------------------------------
    # 2. Beispiel: Revenue
    # --------------------------------------------------

    openbb_value = openbb.get_financial_value(
        dataframe=income,
        symbol=symbol,
        field="revenue",
        fiscal_year=fiscal_year,
    )

    print("=" * 50)
    print("STANDARDIZED OPENBB VALUE")
    print("=" * 50)

    print(openbb_value)

    # --------------------------------------------------
    # 3. SEC Facts laden
    # --------------------------------------------------

    concepts = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ]

    sec_facts = sec.get_facts(
        cik=cik,
        concepts=concepts,
    )

    # --------------------------------------------------
    # 4. Match
    # --------------------------------------------------

    result = matcher.match(
        openbb_value,
        sec_facts,
    )

    print()
    print("MATCH RESULT")
    print("=" * 50)

    print(f"Matched:             {result.matched}")
    print(f"Confidence:          {result.confidence:.2f}")
    print(f"OpenBB value:        {result.openbb_value.value}")

    if result.sec_fact:

        print(
            f"SEC value:           "
            f"{result.sec_fact.value}"
        )

        print(
            f"SEC concept:        "
            f"{result.sec_fact.concept}"
        )

        print(
            f"SEC filing date:    "
            f"{result.sec_fact.filing_date}"
        )

        print(
            f"SEC accession:      "
            f"{result.sec_fact.accession_number}"
        )

    print(
        f"Relative difference: "
        f"{result.relative_difference}"
    )

    print(
        f"Reason:             "
        f"{result.reason}"
    )

if __name__ == "__main__":
    main()