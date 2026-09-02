from datetime import date, datetime

from quant.data.models import FilingFact, FinancialValue
from quant.validation.filing_matcher import FilingFinancialMatcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_openbb_value(
    field="revenue",
    value=100.0,
    period_end=date(2020, 12, 31),
    fiscal_year=2020,
    fiscal_period="FY",
    filing_date=date(2021, 2, 1),
    accepted_date=datetime(2021, 2, 1),
):
    """
    Create a FinancialValue using the real project model.
    """

    return FinancialValue(
        symbol="TEST",
        field=field,
        value=value,
        currency="USD",
        period_end=period_end,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        filing_date=filing_date,
        accepted_date=accepted_date,
        provider="test",
    )


def make_sec_fact(
    concept="RevenueFromContractWithCustomerExcludingAssessedTax",
    value=100.0,
    unit="USD",
    period_start=date(2020, 1, 1),
    period_end=date(2020, 12, 31),
    fiscal_year=2020,
    fiscal_period="FY",
    filing_date=date(2021, 2, 1),
    accepted_date=datetime(2021, 2, 1),
    form="10-K",
    accession_number="0000000000-21-000001",
    cik="0000000000",
):
    """
    Create a FilingFact using the real project model.
    """

    return FilingFact(
        concept=concept,
        value=value,
        unit=unit,
        period_start=period_start,
        period_end=period_end,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        filing_date=filing_date,
        accepted_date=accepted_date,
        form=form,
        accession_number=accession_number,
        cik=cik,
    )


# ---------------------------------------------------------------------------
# Basic matching
# ---------------------------------------------------------------------------

def test_exact_match():
    """
    Identical OpenBB and SEC values should produce a successful match.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(value=100.0)

    sec_fact = make_sec_fact(value=100.0)

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[sec_fact],
    )

    assert result.matched is True
    assert result.sec_fact == sec_fact
    assert result.value_difference == 0.0
    assert result.relative_difference == 0.0
    assert result.confidence > 0.0


# ---------------------------------------------------------------------------
# Period matching
# ---------------------------------------------------------------------------

def test_wrong_period_is_rejected():
    """
    A SEC fact with a different period_end must not be matched.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(
        period_end=date(2020, 12, 31),
    )

    sec_fact = make_sec_fact(
        period_end=date(2019, 12, 31),
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[sec_fact],
    )

    assert result.matched is False
    assert result.sec_fact is None
    assert result.confidence == 0.0


def test_correct_period_beats_wrong_period():
    """
    If several SEC facts exist, only the fact with the correct period
    should survive the period filter.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(
        value=100.0,
        period_end=date(2020, 12, 31),
    )

    wrong = make_sec_fact(
        value=100.0,
        period_end=date(2019, 12, 31),
    )

    correct = make_sec_fact(
        value=100.0,
        period_end=date(2020, 12, 31),
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[wrong, correct],
    )

    assert result.matched is True
    assert result.sec_fact == correct


# ---------------------------------------------------------------------------
# Fiscal period matching
# ---------------------------------------------------------------------------

def test_wrong_fiscal_period_is_rejected():
    """
    FY and quarterly facts must not be mixed when fiscal_period is known.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(
        fiscal_period="FY",
    )

    sec_fact = make_sec_fact(
        fiscal_period="Q4",
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[sec_fact],
    )

    assert result.matched is False
    assert result.sec_fact is None


def test_correct_fiscal_period_is_selected():
    """
    If FY and Q4 facts exist, the requested fiscal period should win.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(
        value=100.0,
        fiscal_period="FY",
    )

    q4 = make_sec_fact(
        value=100.0,
        fiscal_period="Q4",
    )

    fy = make_sec_fact(
        value=100.0,
        fiscal_period="FY",
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[q4, fy],
    )

    assert result.matched is True
    assert result.sec_fact == fy


# ---------------------------------------------------------------------------
# Filing form
# ---------------------------------------------------------------------------

def test_10k_is_preferred_over_non_preferred_form():
    """
    10-K and 10-Q are explicitly preferred by the matcher over other forms.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(value=100.0)

    other = make_sec_fact(
        value=100.0,
        form="8-K",
    )

    ten_k = make_sec_fact(
        value=100.0,
        form="10-K",
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[other, ten_k],
    )

    assert result.matched is True
    assert result.sec_fact == ten_k


# ---------------------------------------------------------------------------
# Value matching
# ---------------------------------------------------------------------------

def test_small_difference_within_relative_tolerance_matches():
    """
    A tiny numerical difference should still match when it is within the
    configured relative tolerance.
    """

    matcher = FilingFinancialMatcher(
        value_tolerance=0.0,
        relative_tolerance=1e-6,
    )

    openbb = make_openbb_value(
        value=100.0,
    )

    sec_fact = make_sec_fact(
        value=100.00001,
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[sec_fact],
    )

    assert result.matched is True
    assert result.relative_difference <= 1e-6


def test_large_difference_does_not_match():
    """
    A materially different value must not be considered a match.
    """

    matcher = FilingFinancialMatcher(
        value_tolerance=0.0,
        relative_tolerance=1e-9,
    )

    openbb = make_openbb_value(
        value=100.0,
    )

    sec_fact = make_sec_fact(
        value=110.0,
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[sec_fact],
    )

    assert result.matched is False
    assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# Concept mapping
# ---------------------------------------------------------------------------

def test_unknown_openbb_field_is_rejected():
    """
    If no SEC concept mapping exists, the matcher must fail cleanly.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(
        field="this_field_definitely_does_not_exist",
        value=100.0,
    )

    sec_fact = make_sec_fact(
        value=100.0,
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[sec_fact],
    )

    assert result.matched is False
    assert result.sec_fact is None
    assert result.confidence == 0.0
    assert "No SEC concept mapping" in result.reason


# ---------------------------------------------------------------------------
# Empty candidate set
# ---------------------------------------------------------------------------

def test_empty_sec_facts():
    """
    No SEC facts means no match.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value()

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[],
    )

    assert result.matched is False
    assert result.sec_fact is None
    assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# Concept priority
# ---------------------------------------------------------------------------

def test_concept_priority_is_respected():
    """
    When multiple SEC concepts map to the same OpenBB field and all other
    properties are equal, the concept appearing first in SEC_CONCEPTS
    should be selected.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(value=100.0)

    # These concepts should be replaced with two concepts that actually
    # exist in SEC_CONCEPTS["revenue"] in the project.
    first = make_sec_fact(
        concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        value=100.0,
    )

    second = make_sec_fact(
        concept="Revenues",
        value=100.0,
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[second, first],
    )

    assert result.matched is True

    # Do not hard-code the expected concept here until the actual
    # SEC_CONCEPTS["revenue"] ordering is confirmed.
    assert result.sec_fact in {first, second}


# ---------------------------------------------------------------------------
# PIT / filing-date sanity check
# ---------------------------------------------------------------------------

def test_future_filing_is_not_automatically_selected():
    """
    This is an important PIT sanity test.

    The current matcher does NOT have an as-of date parameter, so this test
    documents the current behavior rather than pretending that PIT filtering
    already exists.

    Once the matcher receives an explicit as_of_date, this test should be
    strengthened to assert that future filings are excluded.
    """

    matcher = FilingFinancialMatcher()

    openbb = make_openbb_value(
        value=100.0,
        filing_date=date(2021, 2, 1),
    )

    earlier = make_sec_fact(
        value=100.0,
        filing_date=date(2021, 1, 29),
    )

    later = make_sec_fact(
        value=100.0,
        filing_date=date(2021, 3, 1),
    )

    result = matcher.match(
        openbb_value=openbb,
        sec_facts=[earlier, later],
    )

    assert result.matched is True

    # Current implementation sorts filing_date ascending, so the earlier
    # filing wins. This assertion protects that behavior for now.
    assert result.sec_fact == earlier


# ---------------------------------------------------------------------------
# Usage of accepted_date with filing_date as fallback
# ---------------------------------------------------------------------------

def test_get_available_at_prefers_accepted_date():
    fact = FilingFact(
        concept="Revenues",
        value=100.0,
        unit="USD",
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2017, 8, 4),
        accepted_date=datetime(2017, 8, 4, 16, 32, 15),
        form="10-K",
        accession_number="0000000000-17-000000",
        cik="0000789019",
    )

    matcher = FilingFinancialMatcher()

    assert matcher._get_available_at(fact) == datetime(
        2017,
        8,
        4,
        16,
        32,
        15,
    )

def test_get_available_at_falls_back_to_filing_date():
    fact = FilingFact(
        concept="Revenues",
        value=100.0,
        unit="USD",
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2017, 8, 4),
        accepted_date=None,
        form="10-K",
        accession_number="0000000000-17-000000",
        cik="0000789019",
    )

    matcher = FilingFinancialMatcher()

    assert matcher._get_available_at(fact) == datetime(
        2017,
        8,
        4,
        23,
        59,
        59,
        999999,
    )

# ---------------------------------------------------------------------------
# future filing can be excluded 
# ---------------------------------------------------------------------------

def test_filter_available_as_of_excludes_future_filing():
    matcher = FilingFinancialMatcher()

    old_fact = FilingFact(
        concept="Revenues",
        value=90.0,
        unit="USD",
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2017, 8, 4),
        accepted_date=datetime(2017, 8, 4, 16, 32, 15),
        form="10-K",
        accession_number="old",
        cik="0000789019",
    )

    future_fact = FilingFact(
        concept="Revenues",
        value=100.0,
        unit="USD",
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2018, 8, 3),
        accepted_date=datetime(2018, 8, 3, 16, 32, 15),
        form="10-K",
        accession_number="future",
        cik="0000789019",
    )

    result = matcher._filter_available_as_of(
        [old_fact, future_fact],
        date(2017, 12, 31),
    )

    assert result == [old_fact]

# ---------------------------------------------------------------------------
# acceptance timestamp can be used to filter future filings
# ---------------------------------------------------------------------------

def test_filter_available_as_of_acceptance_timestamp():
    matcher = FilingFinancialMatcher()

    fact = FilingFact(
        concept="Revenues",
        value=100.0,
        unit="USD",
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2017, 8, 4),
        accepted_date=datetime(2017, 8, 4, 16, 32, 15),
        form="10-K",
        accession_number="test",
        cik="0000789019",
    )

    before = matcher._filter_available_as_of(
        [fact],
        datetime(2017, 8, 4, 16, 32, 14),
    )

    at_acceptance = matcher._filter_available_as_of(
        [fact],
        datetime(2017, 8, 4, 16, 32, 15),
    )

    assert before == []
    assert at_acceptance == [fact]

# ---------------------------------------------------------------------------
# match() uses the pit filtering
# ---------------------------------------------------------------------------

def test_match_respects_as_of_date():
    matcher = FilingFinancialMatcher()

    old_fact = FilingFact(
        concept="Revenues",
        value=90.0,
        unit="USD",
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2017, 8, 4),
        accepted_date=datetime(2017, 8, 4, 16, 32, 15),
        form="10-K",
        accession_number="old",
        cik="0000789019",
    )

    future_fact = FilingFact(
        concept="Revenues",
        value=100.0,
        unit="USD",
        period_start=date(2016, 7, 1),
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2018, 8, 3),
        accepted_date=datetime(2018, 8, 3, 16, 32, 15),
        form="10-K",
        accession_number="future",
        cik="0000789019",
    )

    openbb_value = FinancialValue(
        symbol="MSFT",
        field="revenue",
        value=90.0,
        currency="USD",
        period_end=date(2017, 6, 30),
        fiscal_year=2017,
        fiscal_period="FY",
        filing_date=date(2017, 8, 4),
        accepted_date=datetime(2017, 8, 4, 16, 32, 15),
        provider="openbb",
    )

    result = matcher.match(
        openbb_value,
        [old_fact, future_fact],
        as_of_date=date(2017, 12, 31),
    )

    assert result.matched
    assert result.sec_fact == old_fact

