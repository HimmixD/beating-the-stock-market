import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from quant.data.provider_bootstrap import build_fundamentals_service


@dataclass
class GoldenCase:
    case_id: str
    symbol: str
    field: str
    fiscal_year: int
    statement: str
    fiscal_period: str
    as_of_iso: str
    expect_success: bool
    expected_min_confidence: float
    expected_provider: str
    expected_source: str
    expected_pit_status: str
    expected_value: float | None
    expected_value_tol: float | None
    expected_accession: str | None
    notes: str


def _none_if_blank(v: str):
    v = (v or "").strip()
    return None if v == "" else v


def _load_cases() -> list[GoldenCase]:
    path = Path("tests/fixtures/pit_golden_cases.csv")
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cases: list[GoldenCase] = []
    for r in rows:
        cases.append(
            GoldenCase(
                case_id=r["case_id"],
                symbol=r["symbol"],
                field=r["field"],
                fiscal_year=int(r["fiscal_year"]),
                statement=r["statement"],
                fiscal_period=r.get("fiscal_period", "FY") or "FY",
                as_of_iso=r["as_of_iso"],
                expect_success=str(r["expect_success"]).lower() == "true",
                expected_min_confidence=float(r.get("expected_min_confidence") or 0.0),
                expected_provider=r.get("expected_provider") or "",
                expected_source=r.get("expected_source") or "",
                expected_pit_status=r.get("expected_pit_status") or "",
                expected_value=float(r["expected_value"]) if _none_if_blank(r.get("expected_value", "")) is not None else None,
                expected_value_tol=float(r["expected_value_tol"]) if _none_if_blank(r.get("expected_value_tol", "")) is not None else None,
                expected_accession=_none_if_blank(r.get("expected_accession", "")),
                notes=r.get("notes", ""),
            )
        )
    return cases


CASES = _load_cases()


@pytest.mark.integration
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_pit_golden_replay(case: GoldenCase):
    svc = build_fundamentals_service()

    as_of = datetime.fromisoformat(case.as_of_iso.replace("Z", "+00:00"))
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    else:
        as_of = as_of.astimezone(timezone.utc)

    if not case.expect_success:
        with pytest.raises(ValueError):
            svc.get_value(
                symbol=case.symbol,
                field=case.field,
                fiscal_year=case.fiscal_year,
                fiscal_period=case.fiscal_period,
                as_of_date=as_of,
                use_cache=False,
            )
        return

    result = svc.get_value(
        symbol=case.symbol,
        field=case.field,
        fiscal_year=case.fiscal_year,
        fiscal_period=case.fiscal_period,
        as_of_date=as_of,
        use_cache=False,
    )

    fv = result.financial_value
    assert fv is not None, f"{case.case_id}: missing financial value"
    assert fv.provider == case.expected_provider, f"{case.case_id}: provider mismatch"
    assert fv.source == case.expected_source, f"{case.case_id}: source mismatch"
    assert fv.pit_status == case.expected_pit_status, f"{case.case_id}: pit_status mismatch"

    # PIT invariant
    if fv.accepted_date is not None:
        assert fv.accepted_date <= as_of, f"{case.case_id}: accepted_date after as_of"

    # Optional strict checks
    if case.expected_value is not None:
        tol = case.expected_value_tol if case.expected_value_tol is not None else 0.0
        assert abs(fv.value - case.expected_value) <= tol, f"{case.case_id}: value mismatch"

    if case.expected_accession is not None:
        assert fv.source_accession == case.expected_accession, f"{case.case_id}: accession mismatch"