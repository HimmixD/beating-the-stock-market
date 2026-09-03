from datetime import date, datetime, timezone, time
from enum import Enum

from ..data.models import (
    FilingFact,
    FinancialValue,
    MatchResult,
)

from .concept_map import SEC_CONCEPTS


class AvailabilityPolicy(str, Enum):
    STRICT_ACCEPTED_ONLY = "strict_accepted_only"
    FILED_DATE_EOD_UTC = "filed_date_eod_utc"


class FilingFinancialMatcher:

    def __init__(
        self,
        value_tolerance: float = 0.0,
        relative_tolerance: float = 1e-9,
        availability_policy: AvailabilityPolicy = AvailabilityPolicy.STRICT_ACCEPTED_ONLY,
    ):
        self.value_tolerance = value_tolerance
        self.relative_tolerance = relative_tolerance
        self.availability_policy = availability_policy

    @staticmethod
    def _to_utc_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _as_datetime_utc(value: date | datetime) -> datetime:
        if isinstance(value, datetime):
            return FilingFinancialMatcher._to_utc_aware(value)
        return datetime.combine(value, time.max, tzinfo=timezone.utc)
    
    @staticmethod
    def _as_of_to_datetime(as_of_date: date | datetime) -> datetime:
        if isinstance(as_of_date, datetime):
            return FilingFinancialMatcher._to_utc_aware(as_of_date)
        # date => end of day UTC (explicit, deterministic)
        return datetime.combine(as_of_date, time.max, tzinfo=timezone.utc)

    def _unit_class(self, unit: str | None) -> str:
        if not unit:
            return "unknown"
        u = unit.upper()
        if u in {"USD", "EUR", "GBP"}:
            return "currency_amount"
        if "SHARE" in u:
            return "shares"
        return "unknown"

    def match(
        self,
        openbb_value: FinancialValue,
        sec_facts: list[FilingFact],
        as_of_date: date | datetime | None = None,
    ) -> MatchResult:

        possible_concepts = SEC_CONCEPTS.get(openbb_value.field, [])
        if not possible_concepts:
            return MatchResult(False, openbb_value, None, None, None, 0.0, "No SEC concept mapping exists.")

        candidates = [fact for fact in sec_facts if fact.concept in possible_concepts]
        candidates = self._filter_period(openbb_value, candidates)
        candidates = self._filter_fiscal_period(openbb_value, candidates)
        fy = openbb_value.fiscal_year
        if fy is not None:
            near = [f for f in candidates if (f.fiscal_year is None or abs(int(f.fiscal_year) - int(fy)) <= 1)]
            if near:
                candidates = near
        candidates = self._filter_form(candidates)
        candidates = self._filter_available_as_of(candidates, as_of_date)

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

        best_candidate = self._select_best_candidate(openbb_value, candidates, as_of_date)

        # unit compatibility guard (P0/P1 safety)
        sec_unit_class = self._unit_class(best_candidate.unit)
        openbb_unit_class = "currency_amount"  # current mapped metrics are currency amounts
        if sec_unit_class != "unknown" and sec_unit_class != openbb_unit_class:
            return MatchResult(
                matched=False,
                openbb_value=openbb_value,
                sec_fact=best_candidate,
                value_difference=None,
                relative_difference=None,
                confidence=0.0,
                reason=f"Unit mismatch: OpenBB={openbb_unit_class}, SEC={sec_unit_class} ({best_candidate.unit})",
            )

        openbb_comparison_value = self._normalize_for_comparison(openbb_value.value, openbb_value.field, "openbb")
        sec_comparison_value = self._normalize_for_comparison(best_candidate.value, openbb_value.field, "sec")

        difference = openbb_comparison_value - sec_comparison_value
        relative_difference = abs(difference) / max(abs(openbb_comparison_value), 1.0)

        matched = (
            abs(difference) <= self.value_tolerance
            or relative_difference <= self.relative_tolerance
        )

        confidence = self._calculate_confidence(openbb_value, best_candidate, matched)

        return MatchResult(
            matched=matched,
            openbb_value=openbb_value,
            sec_fact=best_candidate,
            value_difference=difference,
            relative_difference=relative_difference,
            confidence=confidence,
            reason=("Exact filing match." if matched else "SEC candidate found but values differ."),
        )

    def _filter_form(self, candidates: list[FilingFact]) -> list[FilingFact]:
        preferred_forms = {"10-K", "10-K/A", "10-Q", "10-Q/A"}
        preferred = [fact for fact in candidates if fact.form in preferred_forms]
        return preferred or candidates

    def _filter_period(self, openbb_value: FinancialValue, candidates: list[FilingFact]) -> list[FilingFact]:
        return [fact for fact in candidates if fact.period_end == openbb_value.period_end]

    def _filter_fiscal_period(self, openbb_value: FinancialValue, candidates: list[FilingFact]) -> list[FilingFact]:
        if not openbb_value.fiscal_period:
            return candidates
        return [fact for fact in candidates if fact.fiscal_period == openbb_value.fiscal_period]

    def _filter_available_as_of(
        self,
        candidates: list[FilingFact],
        as_of_date: date | datetime | None,
    ) -> list[FilingFact]:
        if as_of_date is None:
            return candidates

        as_of_dt = self._as_of_to_datetime(as_of_date)
        result = []

        for fact in candidates:
            available_at = self._get_available_at(fact)
            if available_at <= as_of_dt:
                result.append(fact)

        return result

    def _select_best_candidate(
        self,
        openbb_value: FinancialValue,
        candidates: list[FilingFact],
        as_of_date: date | datetime | None = None,
    ) -> FilingFact:
        """
        Ranking strategy:

        1) SEC concept priority (from SEC_CONCEPTS order)
        2) Fiscal-year proximity to OpenBB FY (if available)
        3) Time anchor ranking:
           - PIT mode: latest available fact <= as_of_date
           - non-PIT: closest to OpenBB anchor if known, else earliest available
        4) Stable tiebreakers (form priority, accession_number)
        """

        concept_priority = {
            concept: idx
            for idx, concept in enumerate(SEC_CONCEPTS[openbb_value.field])
        }

        form_priority = {
            "10-K": 0,
            "10-K/A": 1,
            "10-Q": 2,
            "10-Q/A": 3,
        }

        # anchor for non-PIT: OpenBB accepted_date -> filing_date -> period_end EOD
        openbb_anchor: datetime | None = None
        if openbb_value.accepted_date is not None:
            openbb_anchor = self._to_utc_aware(openbb_value.accepted_date)
        elif openbb_value.filing_date is not None:
            openbb_anchor = datetime.combine(
                openbb_value.filing_date,
                time.max,
                tzinfo=timezone.utc,
            )
        else:
            openbb_anchor = datetime.combine(
                openbb_value.period_end,
                time.max,
                tzinfo=timezone.utc,
            )

        as_of_dt = self._as_datetime_utc(as_of_date) if as_of_date is not None else None

        def available_at_utc(f: FilingFact) -> datetime:
            return self._to_utc_aware(self._get_available_at(f))

        def fy_distance(f: FilingFact) -> int:
            if openbb_value.fiscal_year is None or f.fiscal_year is None:
                return 999
            return abs(int(f.fiscal_year) - int(openbb_value.fiscal_year))

        def base_key(f: FilingFact):
            return (
                concept_priority.get(f.concept, 999),
                fy_distance(f),
                form_priority.get(f.form or "", 99),
            )

        if as_of_dt is not None:
            # PIT: pick the most recent known filing at/ before as_of
            ranked = sorted(
                candidates,
                key=lambda f: (
                    *base_key(f),
                    -available_at_utc(f).timestamp(),    # latest first
                    f.accession_number or "",
                ),
            )
            return ranked[0]

        # non-PIT: choose candidate closest to OpenBB anchor;
        # if tie, earlier availability wins (original filing preference)
        ranked = sorted(
            candidates,
            key=lambda f: (
                *base_key(f),
                abs((available_at_utc(f) - openbb_anchor).total_seconds()),
                available_at_utc(f).timestamp(),
                f.accession_number or "",
            ),
        )
        return ranked[0]

    def _get_available_at(self, fact: FilingFact) -> datetime:
        if fact.accepted_date is not None:
            return self._to_utc_aware(fact.accepted_date)

        if fact.filing_date is not None:
            return datetime.combine(
                fact.filing_date,
                time.max,
                tzinfo=timezone.utc,
            )

        return datetime.max.replace(tzinfo=timezone.utc)

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
            score += 0.45

        # Exact fiscal period
        if openbb_value.fiscal_period == sec_fact.fiscal_period:
            score += 0.20

        # Filing date
        if openbb_value.filing_date == sec_fact.filing_date:
            score += 0.10

        # Exact numerical equality
        if openbb_value.value == sec_fact.value:
            score += 0.25

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