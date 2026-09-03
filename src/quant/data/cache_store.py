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
                fiscal_period_key TEXT NOT NULL,
                period_end TEXT,
                filing_date TEXT,
                accepted_date TEXT,
                currency TEXT,
                value REAL NOT NULL,
                fetched_at_utc TEXT NOT NULL,
                PRIMARY KEY (provider, symbol, field, fiscal_year, fiscal_period_key)
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _fp_key(fiscal_period: Optional[str]) -> str:
        return (fiscal_period or "").strip().upper()

    def get(self, provider: str, symbol: str, field: str, fiscal_year: int, fiscal_period: str = "FY") -> FinancialValue | None:
        fp_key = self._fp_key(fiscal_period)
        fiscal_year = int(fiscal_year)
        row = self.conn.execute(
            """
            SELECT symbol, field, value, currency, period_end, fiscal_year,
                   fiscal_period, filing_date, accepted_date, provider
            FROM financial_values
            WHERE provider=? AND symbol=? AND field=? AND fiscal_year=? AND fiscal_period_key=?
            """,
            (provider, symbol.upper(), field, fiscal_year, fp_key),
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
        )

    def put(self, fv: FinancialValue) -> None:
        fp_key = self._fp_key(fv.fiscal_period)

        fiscal_year = int(fv.fiscal_year) if fv.fiscal_year is not None else None
        value = float(fv.value)

        self.conn.execute(
            """
            INSERT OR REPLACE INTO financial_values
            (provider, symbol, field, fiscal_year, fiscal_period, fiscal_period_key,
            period_end, filing_date, accepted_date, currency, value, fetched_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(fv.provider),
                str(fv.symbol).upper(),
                str(fv.field),
                fiscal_year,
                fv.fiscal_period,
                fp_key,
                fv.period_end.isoformat() if fv.period_end else None,
                fv.filing_date.isoformat() if fv.filing_date else None,
                fv.accepted_date.isoformat() if fv.accepted_date else None,
                fv.currency,
                value,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()