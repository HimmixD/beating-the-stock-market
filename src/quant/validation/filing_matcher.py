from datetime import date, datetime

from ..data.models import (
    FilingFact,
    FinancialValue,
    MatchResult,
)

from .concept_map import SEC_CONCEPTS


class FilingFinancialMatcher:

    def __init__(
        self,
        value_tolerance: float = 0.0,
        relative_tolerance: float = 1e-9,
    ):
        self.value_tolerance = value_tolerance
        self.relative_tolerance = relative_tolerance

    def match(
        self,
        openbb_value: FinancialValue,
        sec_facts: list[FilingFact],
        as_of_date: date | datetime | None = None,
    ) -> MatchResult:

        possible_concepts = SEC_CONCEPTS.get(
            openbb_value.field,
            [],
        )

        if not possible_concepts:
            return MatchResult(
                matched=False,
                openbb_value=openbb_value,
                sec_fact=None,
                value_difference=None,
                relative_difference=None,
                confidence=0.0,
                reason="No SEC concept mapping exists.",
            )

        # ---------------------------------------------------------
        # 1. SEC concept
        # ---------------------------------------------------------

        candidates = [
            fact
            for fact in sec_facts
            if fact.concept in possible_concepts
        ]

        # ---------------------------------------------------------
        # 2. Exact period end
        #
        # fiscal_year is intentionally NOT used here.
        # The actual period_end is the authoritative period anchor.
        # ---------------------------------------------------------

        candidates = self._filter_period(
            openbb_value,
            candidates,
        )

        # ---------------------------------------------------------
        # 3. Fiscal period
        #
        # FY/Q1/Q2/Q3 etc. still matters because it describes
        # the type of reporting period.
        # ---------------------------------------------------------

        candidates = self._filter_fiscal_period(
            openbb_value,
            candidates,
        )

        # ---------------------------------------------------------
        # 3.5. form filter
        # ---------------------------------------------------------

        candidates = self._filter_form(
            candidates
        )

        # ---------------------------------------------------------
        # 4. PIT / availability
        # ---------------------------------------------------------

        candidates = self._filter_available_as_of(
            candidates,
            as_of_date,
        )

        if not candidates:
            return MatchResult(
                matched=False,
                openbb_value=openbb_value,
                sec_fact=None,
                value_difference=None,
                relative_difference=None,
                confidence=0.0,
                reason="No SEC fact matched the period and availability constraints.",
            )

        # ---------------------------------------------------------
        # 5. Select best SEC filing
        # ---------------------------------------------------------

        best_candidate = self._select_best_candidate(
            openbb_value,
            candidates,
            as_of_date,
        )

        openbb_comparison_value = self._normalize_for_comparison(
            openbb_value.value,
            openbb_value.field,
            "openbb",
        )

        sec_comparison_value = self._normalize_for_comparison(
            best_candidate.value,
            openbb_value.field,
            "sec",
        )

        difference = (
            openbb_comparison_value
            - sec_comparison_value
        )

        relative_difference = (
            abs(difference)
            / max(abs(openbb_comparison_value), 1.0)
        )

        matched = (
            abs(difference) <= self.value_tolerance
            or relative_difference <= self.relative_tolerance
        )

        print(
            "MATCH DEBUG:",
            openbb_value.field,
            openbb_comparison_value,
            sec_comparison_value,
            difference,
            relative_difference,
            matched,
        )

        confidence = self._calculate_confidence(
            openbb_value,
            best_candidate,
            matched,
        )

        return MatchResult(
            matched=matched,
            openbb_value=openbb_value,
            sec_fact=best_candidate,
            value_difference=difference,
            relative_difference=relative_difference,
            confidence=confidence,
            reason=(
                "Exact filing match."
                if matched
                else "SEC candidate found but values differ."
            ),
        )

    # =============================================================
    # FILTERING
    # =============================================================

    def _filter_form(
        self,
        candidates: list[FilingFact],
    ) -> list[FilingFact]:

        preferred_forms = {
            "10-K",
            "10-K/A",
            "10-Q",
            "10-Q/A",
        }

        preferred = [
            fact
            for fact in candidates
            if fact.form in preferred_forms
        ]

        return preferred or candidates

    def _filter_period(
        self,
        openbb_value: FinancialValue,
        candidates: list[FilingFact],
    ) -> list[FilingFact]:

        return [
            fact
            for fact in candidates
            if fact.period_end == openbb_value.period_end
        ]

    def _filter_fiscal_period(
        self,
        openbb_value: FinancialValue,
        candidates: list[FilingFact],
    ) -> list[FilingFact]:

        if not openbb_value.fiscal_period:
            return candidates

        return [
            fact
            for fact in candidates
            if fact.fiscal_period == openbb_value.fiscal_period
        ]

    def _filter_available_as_of(
        self,
        candidates: list[FilingFact],
        as_of_date: date | datetime | None,
    ) -> list[FilingFact]:

        if as_of_date is None:
            return candidates

        result = []

        for fact in candidates:

            available_at = self._get_available_at(fact)

            if isinstance(as_of_date, datetime):
                if available_at <= as_of_date:
                    result.append(fact)

            else:
                if available_at.date() <= as_of_date:
                    result.append(fact)

        return result

    # =============================================================
    # CANDIDATE SELECTION
    # =============================================================

    def _select_best_candidate(
        self,
        openbb_value,
        candidates,
        as_of_date=None,
    ):
        concept_priority = {
            concept: index
            for index, concept in enumerate(
                SEC_CONCEPTS[openbb_value.field]
            )
        }

        def accepted_timestamp(fact):
            if fact.accepted_date is not None:
                return fact.accepted_date.timestamp()

            if fact.filing_date is not None:
                return datetime.combine(
                    fact.filing_date,
                    datetime.min.time(),
                ).timestamp()

            return float("inf")

        if as_of_date is None:
            # Ohne PIT-Stichtag:
            # ursprüngliche veröffentlichte Version bevorzugen.
            candidates = sorted(
                candidates,
                key=lambda fact: (
                    concept_priority.get(
                        fact.concept,
                        999,
                    ),
                    accepted_timestamp(fact),
                )
            )

        else:
            # _filter_available_as_of() hat bereits alle
            # nach dem Stichtag entfernt.
            #
            # Jetzt die zuletzt bekannte Version wählen.
            candidates = sorted(
                candidates,
                key=lambda fact: (
                    concept_priority.get(
                        fact.concept,
                        999,
                    ),
                    -accepted_timestamp(fact),
                )
            )

        return candidates[0]

    # =============================================================
    # AVAILABILITY
    # =============================================================

    def _get_available_at(
        self,
        fact: FilingFact,
    ) -> datetime:

        """
        Determine when a SEC fact became publicly available.

        accepted_date is preferred because it contains the precise
        SEC acceptance timestamp.

        filing_date is used as fallback.
        """

        if fact.accepted_date is not None:
            return fact.accepted_date

        if fact.filing_date is not None:
            return datetime.combine(
                fact.filing_date,
                datetime.max.time(),
            )

        return datetime.max

    # =============================================================
    # CONFIDENCE
    # =============================================================

    def _calculate_confidence(
        self,
        openbb_value: FinancialValue,
        sec_fact: FilingFact,
        matched: bool,
    ) -> float:

        if not matched:
            return 0.0

        score = 0.0

        # Exact period end
        if openbb_value.period_end == sec_fact.period_end:
            score += 0.35

        # Exact fiscal period
        if openbb_value.fiscal_period == sec_fact.fiscal_period:
            score += 0.15

        # Filing date
        if openbb_value.filing_date == sec_fact.filing_date:
            score += 0.15

        # Exact numerical equality
        if openbb_value.value == sec_fact.value:
            score += 0.15

        return min(score, 1.0)

    # =============================================================
    # VALUE NORMALIZATION
    # =============================================================

    def _normalize_for_comparison(
        self,
        value: float,
        field: str,
        source: str,
    ) -> float:

        if field == "capital_expenditures":
            if source == "openbb":
                return -float(value)

            if source == "sec":
                return float(value)

        return float(value)

    @staticmethod
    def normalize_value(
        value: float,
        unit: str,
    ) -> float:

        unit = unit.upper()

        if unit in {"USD", "EUR", "GBP"}:
            return float(value)

        if unit in {"USD_SHARES", "SHARES"}:
            return float(value)

        return float(value)