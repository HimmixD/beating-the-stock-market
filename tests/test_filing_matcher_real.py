import pytest

from datetime import timedelta, date, datetime, timezone

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
        "expected_accession": "0001193125-15-356351",
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
        "expected_accession": "0001564590-17-014900",
        "as_of_date": datetime(
            2017, 8, 3,
            tzinfo=timezone.utc,
        ),
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

    for fact in sec_facts:
        if (
            fact.accession_number
            == case["expected_accession"]
            and fact.period_end
            == openbb_value.period_end
        ):
            print("\nGROUND TRUTH FILING:")
            print(f"  accession: {fact.accession_number}")
            print(f"  form:      {fact.form}")
            print(f"  filed:     {fact.filing_date}")
            print(f"  accepted:  {fact.accepted_date}")
            print(f"  period:    {fact.period_end}")
            print(f"  value:     {fact.value}")

    result = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=case["as_of_date"],
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
        print(f"SEC accepted_date:   {result.sec_fact.accepted_date}")
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

@pytest.mark.integration
def test_real_msft_fy2017_pit_boundary():
    """
    Real-data PIT boundary test for MSFT FY2017.

    The test uses the real SEC Company Facts data and the real
    OpenBB PIT value.

    The expected SEC filing is:
        accession = 0001564590-17-014900
        filing    = 2017-08-02

    The fact must not be available before its SEC acceptance
    timestamp, but must be available at and after that timestamp.
    """

    symbol = "MSFT"
    cik = "0000789019"
    field = "revenue"
    fiscal_year = 2017
    expected_accession = "0001564590-17-014900"

    openbb_client = OpenBBClient()
    sec_client = SECClient()
    matcher = FilingFinancialMatcher()

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
    # 2. Real SEC Company Facts
    # ---------------------------------------------------------------

    sec_facts = sec_client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    # ---------------------------------------------------------------
    # 3. Find the independently validated filing
    # ---------------------------------------------------------------

    expected_facts = [
        fact
        for fact in sec_facts
        if fact.accession_number == expected_accession
        and fact.period_end == openbb_value.period_end
        and fact.fiscal_year == fiscal_year
    ]

    assert expected_facts, (
        "Expected MSFT FY2017 SEC filing was not found in "
        "Company Facts."
    )

    expected_fact = expected_facts[0]

    assert expected_fact.accepted_date is not None, (
        "SEC fact does not contain accepted_date. "
        "PIT validation cannot be performed safely."
    )

    accepted_at = expected_fact.accepted_date

    # ---------------------------------------------------------------
    # 4. PIT just before SEC acceptance
    # ---------------------------------------------------------------

    before_acceptance = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=accepted_at - timedelta(
            microseconds=1
        ),
    )

    # ---------------------------------------------------------------
    # 5. PIT exactly at SEC acceptance
    # ---------------------------------------------------------------

    at_acceptance = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=accepted_at,
    )

    # ---------------------------------------------------------------
    # 6. PIT after SEC acceptance
    # ---------------------------------------------------------------

    after_acceptance = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=accepted_at + timedelta(
            microseconds=1
        ),
    )

    # ---------------------------------------------------------------
    # 7. Diagnostics
    # ---------------------------------------------------------------

    print("\n" + "=" * 80)
    print("MSFT FY2017 REAL PIT BOUNDARY TEST")
    print("=" * 80)

    print(f"OpenBB value:          {openbb_value.value}")
    print(f"OpenBB period_end:     {openbb_value.period_end}")
    print(f"Expected accession:    {expected_accession}")
    print(f"SEC filing_date:       {expected_fact.filing_date}")
    print(f"SEC accepted_date:     {expected_fact.accepted_date}")

    print("\nBefore acceptance:")
    print(f"  matched:             {before_acceptance.matched}")
    print(f"  reason:              {before_acceptance.reason}")

    print("\nAt acceptance:")
    print(f"  matched:             {at_acceptance.matched}")
    print(f"  reason:              {at_acceptance.reason}")

    if at_acceptance.sec_fact:
        print(
            f"  accession:           "
            f"{at_acceptance.sec_fact.accession_number}"
        )

    print("\nAfter acceptance:")
    print(f"  matched:             {after_acceptance.matched}")
    print(f"  reason:              {after_acceptance.reason}")

    if after_acceptance.sec_fact:
        print(
            f"  accession:           "
            f"{after_acceptance.sec_fact.accession_number}"
        )

    # ---------------------------------------------------------------
    # 8. Assertions
    # ---------------------------------------------------------------

    assert expected_fact.accepted_date == accepted_at

    # Before SEC acceptance the filing must not be available.
    assert before_acceptance.sec_fact is None
    assert before_acceptance.matched is False

    # At SEC acceptance the filing becomes available.
    assert at_acceptance.matched is True
    assert at_acceptance.sec_fact is not None
    assert (
        at_acceptance.sec_fact.accession_number
        == expected_accession
    )

    # After acceptance it must remain available.
    assert after_acceptance.matched is True
    assert after_acceptance.sec_fact is not None
    assert (
        after_acceptance.sec_fact.accession_number
        == expected_accession
    )

@pytest.mark.integration
def test_real_msft_filing_history_contains_fy2017_10k():
    """
    Verify that the SEC submission history contains the
    independently validated MSFT FY2017 10-K and that its
    acceptance timestamp is available.
    """

    sec_client = SECClient()

    filings = sec_client.get_filings(
        cik="0000789019",
    )

    matching_filings = [
        filing
        for filing in filings
        if filing.get("accessionNumber")
        == "0001564590-17-014900"
    ]

    assert len(matching_filings) == 1

    filing = matching_filings[0]

    assert filing["form"] == "10-K"

    assert filing["filingDate"] == "2017-08-02"

    assert filing["reportDate"] == "2017-06-30"

    assert filing["accepted_date"] is not None

    assert (
        filing["accepted_date"].year
        == 2017
    )

    assert (
        filing["accepted_date"].month
        == 8
    )

    assert (
        filing["accepted_date"].day
        == 2
    )

@pytest.mark.integration
def test_real_msft_revenue_filing_versions():
    """
    Diagnostic test.

    Find multiple SEC revenue facts for the same MSFT reporting
    period and display their filing versions and PIT timestamps.

    This test intentionally does not change matcher behavior.
    It helps identify real amendment/version cases for the next
    PIT regression test.
    """

    symbol = "MSFT"
    cik = "0000789019"
    field = "revenue"

    sec_client = SECClient()

    sec_facts = sec_client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    # ---------------------------------------------------------------
    # Group revenue facts by reporting period
    # ---------------------------------------------------------------

    grouped = {}

    for fact in sec_facts:

        key = (
            fact.period_end,
            fact.fiscal_year,
            fact.fiscal_period,
        )

        grouped.setdefault(
            key,
            [],
        ).append(fact)

    # ---------------------------------------------------------------
    # Find periods with multiple filing versions
    # ---------------------------------------------------------------

    version_groups = []

    for key, facts in grouped.items():

        accessions = {
            fact.accession_number
            for fact in facts
            if fact.accession_number
        }

        if len(accessions) > 1:

            version_groups.append(
                (
                    key,
                    facts,
                )
            )

    print("\n" + "=" * 100)
    print("MSFT REAL SEC REVENUE FILING VERSIONS")
    print("=" * 100)

    print(
        f"\nPeriods with multiple accession numbers: "
        f"{len(version_groups)}"
    )

    # ---------------------------------------------------------------
    # Show the first relevant groups
    # ---------------------------------------------------------------

    for (
        period_end,
        fiscal_year,
        fiscal_period,
    ), facts in sorted(
        version_groups,
        key=lambda item: item[0][0],
        reverse=True,
    )[:20]:

        print("\n" + "-" * 100)

        print(
            f"period_end={period_end} "
            f"fy={fiscal_year} "
            f"fp={fiscal_period}"
        )

        unique_facts = {}

        for fact in facts:

            accession = fact.accession_number

            if accession is None:
                continue

            unique_facts[
                (
                    accession,
                    fact.concept,
                    fact.unit,
                )
            ] = fact

        for fact in sorted(
            unique_facts.values(),
            key=lambda item: (
                item.accepted_date
                or datetime.max
            ),
        ):

            print(
                f"concept={fact.concept:50} "
                f"value={fact.value:15,.0f} "
                f"form={str(fact.form):7} "
                f"filed={str(fact.filing_date):10} "
                f"accepted={str(fact.accepted_date):30} "
                f"accn={fact.accession_number}"
            )

    # ---------------------------------------------------------------
    # Diagnostic test must successfully query SEC data.
    # ---------------------------------------------------------------

    assert sec_facts

@pytest.mark.integration
def test_real_amendment_candidates():
    """
    Diagnostic test.

    Search real SEC Company Facts for potential amended filings
    where the same financial fact appears in both an original
    filing and an amended filing.
    """

    cases = [
        {
            "symbol": "AAPL",
            "cik": "0000320193",
        },
        {
            "symbol": "MSFT",
            "cik": "0000789019",
        },
    ]

    for case in cases:

        symbol = case["symbol"]
        cik = case["cik"]

        sec_client = SECClient()

        company_facts = sec_client.get_company_facts(cik)

        us_gaap = (
            company_facts
            .get("facts", {})
            .get("us-gaap", {})
        )

        print("\n" + "=" * 110)
        print(f"{symbol} REAL SEC AMENDMENT CANDIDATES")
        print("=" * 110)

        found = 0

        for concept, concept_data in us_gaap.items():

            units = concept_data.get(
                "units",
                {},
            )

            for unit_name, unit_facts in units.items():

                groups = {}

                for fact in unit_facts:

                    if "end" not in fact:
                        continue

                    if not fact.get("accn"):
                        continue

                    key = (
                        fact.get("start"),
                        fact.get("end"),
                        fact.get("fy"),
                        fact.get("fp"),
                        unit_name,
                    )

                    groups.setdefault(
                        key,
                        [],
                    ).append(fact)

                for key, facts in groups.items():

                    forms = {
                        fact.get("form")
                        for fact in facts
                    }

                    if not (
                        "10-K" in forms
                        and "10-K/A" in forms
                    ) and not (
                        "10-Q" in forms
                        and "10-Q/A" in forms
                    ):
                        continue

                    accessions = {
                        fact.get("accn")
                        for fact in facts
                    }

                    if len(accessions) < 2:
                        continue

                    found += 1

                    print("\n" + "-" * 110)

                    print(
                        f"concept={concept}"
                    )

                    print(
                        f"period={key[0]} -> {key[1]} "
                        f"fy={key[2]} "
                        f"fp={key[3]} "
                        f"unit={key[4]}"
                    )

                    for fact in sorted(
                        facts,
                        key=lambda item: (
                            item.get("filed")
                            or ""
                        ),
                    ):

                        if fact.get("form") not in {
                            "10-K",
                            "10-K/A",
                            "10-Q",
                            "10-Q/A",
                        }:
                            continue

                        print(
                            f"form={fact.get('form'):6} "
                            f"value={float(fact['val']):20,.2f} "
                            f"filed={fact.get('filed')} "
                            f"accn={fact.get('accn')}"
                        )

        print(
            f"\nPotential amendment groups found: {found}"
        )

        assert found >= 0

@pytest.mark.integration
def test_real_amendment_candidates_summary():
    """
    Diagnostic test.

    Find real 10-K/A and 10-Q/A amendment candidates and print
    only a compact summary instead of dumping the full SEC dataset.
    """

    cases = [
        {
            "symbol": "AAPL",
            "cik": "0000320193",
        },
        {
            "symbol": "MSFT",
            "cik": "0000789019",
        },
    ]

    all_candidates = []

    for case in cases:

        symbol = case["symbol"]
        cik = case["cik"]

        sec_client = SECClient()

        company_facts = sec_client.get_company_facts(cik)

        us_gaap = (
            company_facts
            .get("facts", {})
            .get("us-gaap", {})
        )

        for concept, concept_data in us_gaap.items():

            units = concept_data.get(
                "units",
                {},
            )

            for unit_name, unit_facts in units.items():

                groups = {}

                for fact in unit_facts:

                    if "end" not in fact:
                        continue

                    if not fact.get("accn"):
                        continue

                    form = fact.get("form")

                    if form not in {
                        "10-K",
                        "10-K/A",
                        "10-Q",
                        "10-Q/A",
                    }:
                        continue

                    key = (
                        fact.get("start"),
                        fact.get("end"),
                        fact.get("fy"),
                        fact.get("fp"),
                        unit_name,
                    )

                    groups.setdefault(
                        key,
                        [],
                    ).append(fact)

                for key, facts in groups.items():

                    forms = {
                        fact.get("form")
                        for fact in facts
                    }

                    has_k_amendment = (
                        "10-K" in forms
                        and "10-K/A" in forms
                    )

                    has_q_amendment = (
                        "10-Q" in forms
                        and "10-Q/A" in forms
                    )

                    if not (
                        has_k_amendment
                        or has_q_amendment
                    ):
                        continue

                    original = [
                        fact
                        for fact in facts
                        if fact.get("form")
                        in {"10-K", "10-Q"}
                    ]

                    amendments = [
                        fact
                        for fact in facts
                        if fact.get("form")
                        in {"10-K/A", "10-Q/A"}
                    ]

                    if not original or not amendments:
                        continue

                    for amendment in amendments:

                        # Find the corresponding original
                        # filing with the same reporting period.
                        matching_originals = [
                            fact
                            for fact in original
                            if fact.get("accn")
                            != amendment.get("accn")
                        ]

                        if not matching_originals:
                            continue

                        original_fact = min(
                            matching_originals,
                            key=lambda fact: (
                                fact.get("filed")
                                or ""
                            ),
                        )

                        all_candidates.append(
                            {
                                "symbol": symbol,
                                "concept": concept,
                                "unit": unit_name,
                                "start": key[0],
                                "end": key[1],
                                "fy": key[2],
                                "fp": key[3],
                                "original_form": original_fact.get(
                                    "form"
                                ),
                                "original_value": float(
                                    original_fact["val"]
                                ),
                                "original_filed": original_fact.get(
                                    "filed"
                                ),
                                "original_accn": original_fact.get(
                                    "accn"
                                ),
                                "amendment_form": amendment.get(
                                    "form"
                                ),
                                "amendment_value": float(
                                    amendment["val"]
                                ),
                                "amendment_filed": amendment.get(
                                    "filed"
                                ),
                                "amendment_accn": amendment.get(
                                    "accn"
                                ),
                            }
                        )

    # ---------------------------------------------------------------
    # Sort by amendment filing date
    # ---------------------------------------------------------------

    all_candidates.sort(
        key=lambda candidate: (
            candidate["amendment_value"]
            != candidate["original_value"],
            candidate["amendment_filed"] or "",
        ),
        reverse=True,
    )

    print("\n" + "=" * 110)
    print("REAL SEC AMENDMENT CANDIDATES")
    print("=" * 110)

    print(
        f"\nTotal candidates: {len(all_candidates)}"
    )

    # Only show the first 30 candidates.
    for candidate in all_candidates[:30]:

        print("\n" + "-" * 110)

        print(
            f"{candidate['symbol']} | "
            f"{candidate['concept']} | "
            f"{candidate['unit']}"
        )

        print(
            f"period: "
            f"{candidate['start']} -> "
            f"{candidate['end']} | "
            f"FY={candidate['fy']} | "
            f"FP={candidate['fp']}"
        )

        print(
            f"ORIGINAL: "
            f"{candidate['original_form']} | "
            f"value={candidate['original_value']:,.0f} | "
            f"filed={candidate['original_filed']} | "
            f"accn={candidate['original_accn']}"
        )

        print(
            f"AMENDMENT: "
            f"{candidate['amendment_form']} | "
            f"value={candidate['amendment_value']:,.0f} | "
            f"filed={candidate['amendment_filed']} | "
            f"accn={candidate['amendment_accn']}"
        )

        difference = (
            candidate["amendment_value"]
            - candidate["original_value"]
        )

        print(
            f"VALUE DIFFERENCE: "
            f"{difference:,.0f}"
        )

    assert all_candidates

@pytest.mark.integration
def test_real_mapped_amendment_candidates():
    """
    Diagnostic test.

    Find real 10-K -> 10-K/A or 10-Q -> 10-Q/A cases for SEC
    concepts that are actually used by the Filing Matcher.
    """

    cases = [
        {
            "symbol": "AAPL",
            "cik": "0000320193",
        },
        {
            "symbol": "MSFT",
            "cik": "0000789019",
        },
    ]

    mapped_concepts = {
        concept
        for concepts in SEC_CONCEPTS.values()
        for concept in concepts
    }

    candidates = []

    for case in cases:

        symbol = case["symbol"]
        cik = case["cik"]

        sec_client = SECClient()

        company_facts = sec_client.get_company_facts(cik)

        us_gaap = (
            company_facts
            .get("facts", {})
            .get("us-gaap", {})
        )

        for concept in mapped_concepts:

            if concept not in us_gaap:
                continue

            concept_data = us_gaap[concept]

            for unit_name, unit_facts in (
                concept_data.get("units", {}).items()
            ):

                groups = {}

                for fact in unit_facts:

                    if fact.get("form") not in {
                        "10-K",
                        "10-K/A",
                        "10-Q",
                        "10-Q/A",
                    }:
                        continue

                    if not fact.get("accn"):
                        continue

                    key = (
                        fact.get("start"),
                        fact.get("end"),
                        fact.get("fy"),
                        fact.get("fp"),
                        unit_name,
                    )

                    groups.setdefault(
                        key,
                        [],
                    ).append(fact)

                for key, facts in groups.items():

                    originals = [
                        fact
                        for fact in facts
                        if fact.get("form")
                        in {"10-K", "10-Q"}
                    ]

                    amendments = [
                        fact
                        for fact in facts
                        if fact.get("form")
                        in {"10-K/A", "10-Q/A"}
                    ]

                    if not originals or not amendments:
                        continue

                    for amendment in amendments:

                        matching_originals = [
                            fact
                            for fact in originals
                            if fact.get("accn")
                            != amendment.get("accn")
                        ]

                        if not matching_originals:
                            continue

                        original = min(
                            matching_originals,
                            key=lambda fact: (
                                fact.get("filed") or ""
                            ),
                        )

                        original_value = float(
                            original["val"]
                        )

                        amendment_value = float(
                            amendment["val"]
                        )

                        if (
                            original_value
                            == amendment_value
                        ):
                            continue

                        candidates.append(
                            {
                                "symbol": symbol,
                                "concept": concept,
                                "unit": unit_name,
                                "start": key[0],
                                "end": key[1],
                                "fy": key[2],
                                "fp": key[3],
                                "original_form": original.get(
                                    "form"
                                ),
                                "original_value": original_value,
                                "original_filed": original.get(
                                    "filed"
                                ),
                                "original_accn": original.get(
                                    "accn"
                                ),
                                "amendment_form": amendment.get(
                                    "form"
                                ),
                                "amendment_value": amendment_value,
                                "amendment_filed": amendment.get(
                                    "filed"
                                ),
                                "amendment_accn": amendment.get(
                                    "accn"
                                ),
                            }
                        )

    candidates.sort(
        key=lambda candidate: (
            candidate["amendment_filed"] or ""
        ),
        reverse=True,
    )

    print("\n" + "=" * 110)
    print("MAPPED SEC AMENDMENT CANDIDATES")
    print("=" * 110)

    print(
        f"\nMapped concepts with changed amendment values: "
        f"{len(candidates)}"
    )

    for candidate in candidates[:20]:

        print("\n" + "-" * 110)

        print(
            f"{candidate['symbol']} | "
            f"{candidate['concept']} | "
            f"{candidate['unit']}"
        )

        print(
            f"period: "
            f"{candidate['start']} -> "
            f"{candidate['end']} | "
            f"FY={candidate['fy']} | "
            f"FP={candidate['fp']}"
        )

        print(
            f"ORIGINAL: "
            f"{candidate['original_form']} | "
            f"value={candidate['original_value']:,.0f} | "
            f"filed={candidate['original_filed']} | "
            f"accn={candidate['original_accn']}"
        )

        print(
            f"AMENDMENT: "
            f"{candidate['amendment_form']} | "
            f"value={candidate['amendment_value']:,.0f} | "
            f"filed={candidate['amendment_filed']} | "
            f"accn={candidate['amendment_accn']}"
        )

        print(
            f"VALUE DIFFERENCE: "
            f"{candidate['amendment_value'] - candidate['original_value']:,.0f}"
        )

    assert candidates

@pytest.mark.integration
def test_real_aapl_revenue_pit_boundary():
    """
    Validate point-in-time behavior for AAPL FY2009 revenue.

    The original 10-K was filed in October 2009.
    The 10-K/A amendment was filed in January 2010.

    The matcher must therefore select:

        before original filing
            -> no available SEC fact

        after original, before amendment
            -> original 10-K

        after amendment
            -> amended 10-K/A
    """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    symbol = "AAPL"
    cik = "0000320193"
    field = "revenue"
    fiscal_year = 2009

    original_accession = "0001193125-09-214859"
    amendment_accession = "0001193125-10-012091"

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    openbb_client = OpenBBClient()
    sec_client = SECClient()
    matcher = FilingFinancialMatcher()

    # ------------------------------------------------------------------
    # 1. OpenBB PIT data
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

    # ------------------------------------------------------------------
    # 2. SEC Company Facts
    # ------------------------------------------------------------------

    sec_facts = sec_client.get_facts(
        cik=cik,
        concepts=SEC_CONCEPTS[field],
    )

    # ------------------------------------------------------------------
    # 3. Find the original filing and amendment
    # ------------------------------------------------------------------

    relevant_facts = [
        fact
        for fact in sec_facts
        if (
            fact.concept in SEC_CONCEPTS[field]
            and fact.period_end == openbb_value.period_end
            and fact.fiscal_year == openbb_value.fiscal_year
        )
    ]

    original_fact = next(
        fact
        for fact in relevant_facts
        if fact.accession_number == original_accession
    )

    amendment_fact = next(
        fact
        for fact in relevant_facts
        if fact.accession_number == amendment_accession
    )

    # ------------------------------------------------------------------
    # 4. Validate acceptance timestamps
    # ------------------------------------------------------------------

    assert original_fact.accepted_date is not None, (
        "Original SEC fact does not contain accepted_date."
    )

    assert amendment_fact.accepted_date is not None, (
        "Amendment SEC fact does not contain accepted_date."
    )

    original_accepted = original_fact.accepted_date
    amendment_accepted = amendment_fact.accepted_date

    assert amendment_accepted > original_accepted

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    print("\n" + "=" * 100)
    print("AAPL REAL SEC REVENUE PIT BOUNDARY")
    print("=" * 100)

    print("\nOpenBB:")
    print(f"  value:         {openbb_value.value}")
    print(f"  period_end:    {openbb_value.period_end}")
    print(f"  fiscal_year:   {openbb_value.fiscal_year}")
    print(f"  fiscal_period: {openbb_value.fiscal_period}")

    print("\nOriginal filing:")
    print(f"  value:         {original_fact.value}")
    print(f"  form:          {original_fact.form}")
    print(f"  filed:         {original_fact.filing_date}")
    print(f"  accepted:      {original_fact.accepted_date}")
    print(f"  accession:     {original_fact.accession_number}")

    print("\nAmendment:")
    print(f"  value:         {amendment_fact.value}")
    print(f"  form:          {amendment_fact.form}")
    print(f"  filed:         {amendment_fact.filing_date}")
    print(f"  accepted:      {amendment_fact.accepted_date}")
    print(f"  accession:     {amendment_fact.accession_number}")

    # ------------------------------------------------------------------
    # 5. PIT boundary #1
    #    Before original filing
    # ------------------------------------------------------------------

    before_original = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=original_accepted - timedelta(seconds=1),
    )

    print("\nBefore original filing:")
    print(f"  matched:       {before_original.matched}")
    print(f"  confidence:    {before_original.confidence}")
    print(f"  reason:        {before_original.reason}")

    assert before_original.matched is False

    # ------------------------------------------------------------------
    # 6. PIT boundary #2
    #    After original, before amendment
    # ------------------------------------------------------------------

    between_filings = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=(
            original_accepted
            + (amendment_accepted - original_accepted) / 2
        ),
    )

    print("\nBetween original and amendment:")
    print(f"  matched:       {between_filings.matched}")
    print(f"  confidence:    {between_filings.confidence}")
    print(f"  reason:        {between_filings.reason}")

    if between_filings.sec_fact:
        print(
            f"  accession:     "
            f"{between_filings.sec_fact.accession_number}"
        )
        print(
            f"  form:          "
            f"{between_filings.sec_fact.form}"
        )
        print(
            f"  value:         "
            f"{between_filings.sec_fact.value}"
        )

    assert between_filings.matched is True
    assert between_filings.sec_fact is not None

    assert (
        between_filings.sec_fact.accession_number
        == original_accession
    )

    # ------------------------------------------------------------------
    # 7. PIT boundary #3
    #    After amendment
    # ------------------------------------------------------------------

    after_amendment = matcher.match(
        openbb_value=openbb_value,
        sec_facts=sec_facts,
        as_of_date=amendment_accepted,
    )

    print("\nAfter amendment:")
    print(f"  matched:       {after_amendment.matched}")
    print(f"  confidence:    {after_amendment.confidence}")
    print(f"  reason:        {after_amendment.reason}")

    if after_amendment.sec_fact:
        print(
            f"  accession:     "
            f"{after_amendment.sec_fact.accession_number}"
        )
        print(
            f"  form:          "
            f"{after_amendment.sec_fact.form}"
        )
        print(
            f"  value:         "
            f"{after_amendment.sec_fact.value}"
        )

    assert after_amendment.sec_fact is not None

    assert (
        after_amendment.sec_fact.accession_number
        == amendment_accession
    )

    assert (
        after_amendment.sec_fact.form
        == "10-K/A"
    )

    assert (
        after_amendment.sec_fact.value
        == amendment_fact.value
    )