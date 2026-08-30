from dataclasses import dataclass
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
    ) -> MatchResult:

        possible_concepts = SEC_CONCEPTS.get(
            openbb_value.field,
            []
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

        candidates = [
            fact
            for fact in sec_facts
            if fact.concept in possible_concepts
        ]

        candidates = self._filter_period(
            openbb_value,
            candidates
        )

        candidates = self._filter_fiscal_period(
            openbb_value,
            candidates
        )

        candidates = self._filter_form(
            candidates
        )

        if not candidates:

            return MatchResult(
                matched=False,
                openbb_value=openbb_value,
                sec_fact=None,
                value_difference=None,
                relative_difference=None,
                confidence=0.0,
                reason="No SEC fact matched the period.",
            )

        best_candidate = self._select_best_candidate(
            openbb_value,
            candidates
        )

        difference = (
            openbb_value.value
            - best_candidate.value
        )

        relative_difference = (
            abs(difference)
            / max(abs(openbb_value.value), 1.0)
        )

        matched = (
            abs(difference)
            <= self.value_tolerance
            or relative_difference
            <= self.relative_tolerance
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
                "Exact PIT filing match."
                if matched
                else "SEC candidate found but values differ."
            ),
        )

    def _filter_period(
        self,
        openbb_value,
        candidates,
    ):

        return [
            fact
            for fact in candidates
            if fact.period_end
            == openbb_value.period_end
        ]

    def _filter_fiscal_period(
        self,
        openbb_value,
        candidates,
    ):

        if not openbb_value.fiscal_period:
            return candidates

        return [
            fact
            for fact in candidates
            if fact.fiscal_period
            == openbb_value.fiscal_period
        ]

    def _filter_form(
        self,
        candidates,
    ):

        preferred_forms = {
            "10-K",
            "10-Q",
        }

        preferred = [
            fact
            for fact in candidates
            if fact.form in preferred_forms
        ]

        return preferred or candidates

    def _select_best_candidate(
        self,
        openbb_value,
        candidates,
    ):

        concept_priority = {
            concept: index
            for index, concept
            in enumerate(
                SEC_CONCEPTS[
                    openbb_value.field
                ]
            )
        }

        candidates = sorted(
            candidates,
            key=lambda fact: (
                concept_priority.get(
                    fact.concept,
                    999
                ),
                fact.filing_date or date.min,
            )
        )

        return candidates[0]

    def _calculate_confidence(
        self,
        openbb_value,
        sec_fact,
        matched,
    ):

        if not matched:
            return 0.0

        score = 0.0

        # Period matches
        if (
            openbb_value.period_end
            == sec_fact.period_end
        ):
            score += 0.35

        # Fiscal year
        if (
            openbb_value.fiscal_year
            == sec_fact.fiscal_year
        ):
            score += 0.20

        # Fiscal period
        if (
            openbb_value.fiscal_period
            == sec_fact.fiscal_period
        ):
            score += 0.15

        # Filing date
        if (
            openbb_value.filing_date
            == sec_fact.filing_date
        ):
            score += 0.15

        # Exact numerical equality
        if (
            openbb_value.value
            == sec_fact.value
        ):
            score += 0.15

        return min(score, 1.0)

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