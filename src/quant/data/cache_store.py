from __future__ import annotations

import sqlite3
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Optional

from quant.data.models import FinancialValue


class FinancialValueCache:
    def __init__(self, db_path: str = ".cache/fundamentals.sqlite"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_values (
                provider TEXT NOT NULL,
                symbol TEXT NOT NULL,
                field TEXT NOT NULL,
                fiscal_year INTEGER NOT NULL,
                fiscal_period TEXT,
                as_of_key TEXT NOT NULL,              -- NEW
                period_end TEXT,
                filing_date TEXT,
                accepted_date TEXT,
                currency TEXT,
                value REAL NOT NULL,
                source TEXT,
                pit_status TEXT,
                confidence REAL,
                source_concept TEXT,
                source_unit TEXT,
                source_form TEXT,
                source_accession TEXT,
                source_cik TEXT,
                fetched_at_utc TEXT NOT NULL,
                PRIMARY KEY (provider, symbol, field, fiscal_year, fiscal_period, as_of_key)
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _as_of_key(as_of_date: Optional[date | datetime]) -> str:
        if as_of_date is None:
            return "NONE"
        if isinstance(as_of_date, datetime):
            dt = as_of_date if as_of_date.tzinfo else as_of_date.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        return datetime.combine(as_of_date, datetime.max.time(), tzinfo=timezone.utc).isoformat()

    def get(
        self,
        provider: str,
        symbol: str,
        field: str,
        fiscal_year: int,
        fiscal_period: str = "FY",
        as_of_date: Optional[date | datetime] = None,
    ) -> FinancialValue | None:
        as_of_key = self._as_of_key(as_of_date)

        row = self.conn.execute(
            """
            SELECT symbol, field, value, currency, period_end, fiscal_year, fiscal_period,
                   filing_date, accepted_date, provider, source, pit_status, confidence,
                   source_concept, source_unit, source_form, source_accession, source_cik
            FROM financial_values
            WHERE provider=? AND symbol=? AND field=? AND fiscal_year=? AND fiscal_period=? AND as_of_key=?
            """,
            (provider, symbol.upper(), field, fiscal_year, fiscal_period, as_of_key),
        ).fetchone()

        if not row:
            return None

        return FinancialValue(
            symbol=row[0],
            field=row[1],
            value=float(row[2]),
            currency=row[3],
            period_end=date.fromisoformat(row[4]) if row[4] else None,
            fiscal_year=row[5],
            fiscal_period=row[6],
            filing_date=date.fromisoformat(row[7]) if row[7] else None,
            accepted_date=datetime.fromisoformat(row[8]) if row[8] else None,
            provider=row[9],
            source=row[10] or "unknown",
            pit_status=row[11] or "unknown",
            confidence=float(row[12] or 0.0),
            source_concept=row[13],
            source_unit=row[14],
            source_form=row[15],
            source_accession=row[16],
            source_cik=row[17],
        )

    def put(self, fv: FinancialValue, as_of_date: Optional[date | datetime] = None) -> None:
        as_of_key = self._as_of_key(as_of_date)
        fiscal_year = int(fv.fiscal_year) if fv.fiscal_year is not None else None

        self.conn.execute(
            """
            INSERT OR REPLACE INTO financial_values
            (provider, symbol, field, fiscal_year, fiscal_period, as_of_key,
             period_end, filing_date, accepted_date, currency, value,
             source, pit_status, confidence, source_concept, source_unit, source_form,
             source_accession, source_cik, fetched_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(fv.provider),
                str(fv.symbol).upper(),
                str(fv.field),
                fiscal_year,
                fv.fiscal_period or "FY",
                as_of_key,
                fv.period_end.isoformat() if fv.period_end else None,
                fv.filing_date.isoformat() if fv.filing_date else None,
                fv.accepted_date.isoformat() if fv.accepted_date else None,
                fv.currency,
                float(fv.value),
                fv.source,
                fv.pit_status,
                float(fv.confidence),
                fv.source_concept,
                fv.source_unit,
                fv.source_form,
                fv.source_accession,
                fv.source_cik,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()