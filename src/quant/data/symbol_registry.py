from __future__ import annotations

import sqlite3
from pathlib import Path
import requests


SEC_TICKER_CIK_URL = "https://www.sec.gov/files/company_tickers.json"


class SymbolRegistry:
    def __init__(self, db_path: str = ".cache/fundamentals.sqlite"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS symbol_identity (
                symbol TEXT PRIMARY KEY,
                cik TEXT,
                country TEXT,
                exchange TEXT,
                source TEXT
            )
            """
        )
        self.conn.commit()

    def get_cik(self, symbol: str) -> str | None:
        symbol = symbol.upper()
        row = self.conn.execute(
            "SELECT cik FROM symbol_identity WHERE symbol=?",
            (symbol,),
        ).fetchone()
        if row and row[0]:
            return row[0]
        return None

    def upsert(self, symbol: str, cik: str | None, country: str | None, exchange: str | None, source: str):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO symbol_identity (symbol, cik, country, exchange, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (symbol.upper(), cik, country, exchange, source),
        )
        self.conn.commit()

    def refresh_sec_ticker_map(self, user_agent: str):
        headers = {"User-Agent": user_agent}
        resp = requests.get(SEC_TICKER_CIK_URL, headers=headers, timeout=(5, 20))
        resp.raise_for_status()
        data = resp.json()

        for _, row in data.items():
            symbol = str(row.get("ticker", "")).upper().strip()
            cik_num = row.get("cik_str")
            if not symbol or cik_num is None:
                continue
            cik = str(cik_num).zfill(10)
            self.upsert(symbol, cik, "US", None, "sec_ticker_file")