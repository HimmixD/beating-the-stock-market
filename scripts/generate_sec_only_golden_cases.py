from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from quant.data.sec_client import SECClient
from quant.validation.concept_map import SEC_CONCEPTS


@dataclass
class GoldenRow:
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
    expected_value: Optional[float]
    expected_value_tol: Optional[float]
    expected_accession: Optional[str]
    notes: str


STATEMENT_BY_FIELD = {
    "revenue": "income",
    "gross_profit": "income",
    "operating_income": "income",
    "net_income": "income",
    "total_assets": "balance",
    "total_liabilities": "balance",
    "stockholders_equity": "balance",
    "cash_and_cash_equivalents": "balance",
    "operating_cash_flow": "cash",
    "capital_expenditures": "cash",
}


def to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def pick_best_fact_sec_only(facts, fiscal_year: int, fiscal_period: str = "FY"):
    # strict FY/FP first
    strict = [
        f for f in facts
        if f.fiscal_year == fiscal_year and (f.fiscal_period == fiscal_period or f.fiscal_period is None)
    ]
    cands = strict if strict else [f for f in facts if f.fiscal_year is None or abs(int(f.fiscal_year) - fiscal_year) <= 1]

    # must have accepted_date for PIT-authoritative golden rows
    cands = [f for f in cands if to_utc(f.accepted_date) is not None]
    if not cands:
        return None

    form_prio = {"10-K": 0, "10-K/A": 1, "10-Q": 2, "10-Q/A": 3}
    cands = sorted(
        cands,
        key=lambda f: (
            form_prio.get((f.form or ""), 99),
            -to_utc(f.accepted_date).timestamp(),
            f.accession_number or "",
        ),
    )
    return cands[0]


def make_rows_for_case(symbol: str, cik: str, field: str, fiscal_year: int, fiscal_period: str = "FY"):
    client = SECClient()
    concepts = SEC_CONCEPTS[field]
    facts = client.get_facts(cik=cik, concepts=concepts)

    best = pick_best_fact_sec_only(facts, fiscal_year=fiscal_year, fiscal_period=fiscal_period)
    if best is None:
        return []

    accepted = to_utc(best.accepted_date)
    before = accepted - timedelta(seconds=1)
    at_time = accepted
    after = accepted + timedelta(seconds=1)

    statement = STATEMENT_BY_FIELD[field]
    base = f"{symbol.lower()}_{fiscal_year}_{field}"

    rows = [
        GoldenRow(
            case_id=f"{base}_before_accept",
            symbol=symbol,
            field=field,
            fiscal_year=fiscal_year,
            statement=statement,
            fiscal_period=fiscal_period,
            as_of_iso=before.isoformat(),
            expect_success=False,
            expected_min_confidence=0.0,
            expected_provider="sec",
            expected_source="sec_fact",
            expected_pit_status="authoritative",
            expected_value=None,
            expected_value_tol=None,
            expected_accession=None,
            notes="SEC-only boundary: one second before accepted_date must fail.",
        ),
        GoldenRow(
            case_id=f"{base}_at_accept",
            symbol=symbol,
            field=field,
            fiscal_year=fiscal_year,
            statement=statement,
            fiscal_period=fiscal_period,
            as_of_iso=at_time.isoformat(),
            expect_success=True,
            expected_min_confidence=1.0,
            expected_provider="sec",
            expected_source="sec_fact",
            expected_pit_status="authoritative",
            expected_value=float(best.value),
            expected_value_tol=0.0,
            expected_accession=best.accession_number,
            notes=f"SEC-only boundary: at accepted_date. concept={best.concept}, form={best.form}",
        ),
        GoldenRow(
            case_id=f"{base}_after_accept",
            symbol=symbol,
            field=field,
            fiscal_year=fiscal_year,
            statement=statement,
            fiscal_period=fiscal_period,
            as_of_iso=after.isoformat(),
            expect_success=True,
            expected_min_confidence=1.0,
            expected_provider="sec",
            expected_source="sec_fact",
            expected_pit_status="authoritative",
            expected_value=float(best.value),
            expected_value_tol=0.0,
            expected_accession=best.accession_number,
            notes=f"SEC-only boundary: after accepted_date. concept={best.concept}, form={best.form}",
        ),
    ]
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate SEC-only PIT golden cases CSV.")
    parser.add_argument("--out", default="tests/fixtures/pit_golden_cases.csv")
    parser.add_argument("--fiscal-period", default="FY")
    args = parser.parse_args()

    # Edit/extend this list as needed
    targets = [
        ("AAPL", "0000320193", 2009, ["revenue", "total_assets", "operating_cash_flow"]),
        ("MSFT", "0000789019", 2017, ["revenue", "total_assets", "operating_cash_flow"]),
        ("AMZN", "0001018724", 2008, ["revenue", "total_assets"]),
    ]

    all_rows: list[GoldenRow] = []
    for symbol, cik, fy, fields in targets:
        for field in fields:
            if field not in SEC_CONCEPTS:
                continue
            rows = make_rows_for_case(symbol, cik, field, fy, fiscal_period=args.fiscal_period)
            all_rows.extend(rows)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "case_id", "symbol", "field", "fiscal_year", "statement", "fiscal_period",
        "as_of_iso", "expect_success", "expected_min_confidence", "expected_provider",
        "expected_source", "expected_pit_status", "expected_value", "expected_value_tol",
        "expected_accession", "notes"
    ]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in all_rows:
            writer.writerow([
                r.case_id,
                r.symbol,
                r.field,
                r.fiscal_year,
                r.statement,
                r.fiscal_period,
                r.as_of_iso,
                str(r.expect_success).lower(),
                r.expected_min_confidence,
                r.expected_provider,
                r.expected_source,
                r.expected_pit_status,
                "" if r.expected_value is None else f"{r.expected_value:.10f}",
                "" if r.expected_value_tol is None else r.expected_value_tol,
                "" if r.expected_accession is None else r.expected_accession,
                r.notes,
            ])

    print(f"Wrote {len(all_rows)} golden rows to: {out}")
    print("Copy/paste-ready CSV generated from SEC facts only.")


if __name__ == "__main__":
    main()