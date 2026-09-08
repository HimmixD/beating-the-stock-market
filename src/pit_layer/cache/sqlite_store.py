import sqlite3
from typing import Optional, List, Tuple

class SQLiteStore:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticker_mapping (
                    ticker TEXT PRIMARY KEY,
                    cik TEXT,
                    provider TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_facts (
                    ticker TEXT,
                    concept TEXT,
                    val REAL,
                    fy INTEGER,
                    fp TEXT,
                    filed TEXT,
                    accepted TEXT,
                    form TEXT,
                    accession TEXT,
                    provider TEXT,
                    PRIMARY KEY (ticker, concept, fy, fp, accepted, provider)
                )
            """)
            conn.commit()

    def save_mapping(self, ticker: str, cik: str, provider: str = "sec"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ticker_mapping (ticker, cik, provider) VALUES (?, ?, ?)",
                (ticker, cik, provider)
            )

    def get_cik(self, ticker: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            res = conn.execute("SELECT cik FROM ticker_mapping WHERE ticker = ?", (ticker,)).fetchone()
            return res[0] if res else None

    def save_facts(self, records: List[Tuple]):
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO financial_facts 
                (ticker, concept, val, fy, fp, filed, accepted, form, accession, provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

    def get_pit_value(self, ticker: str, concept: str, year: int, period: str, as_of_date: Optional[str]) -> Optional[dict]:
        # Wir filtern nun primär nach dem exakten accepted-Timestamp für micro-precision PIT
        query = """
            SELECT val, filed, accepted, form, accession FROM financial_facts 
            WHERE ticker = ? AND concept = ? AND fy = ? AND fp = ?
        """
        params = [ticker, concept, year, period]

        if as_of_date:
            query += " AND accepted <= ?"
            params.append(as_of_date)

        query += " ORDER BY accepted DESC LIMIT 1"

        with sqlite3.connect(self.db_path) as conn:
            res = conn.execute(query, params).fetchone()
            if res:
                return {
                    "val": res[0],
                    "filed": res[1],
                    "accepted": res[2],
                    "form": res[3],
                    "accession": res[4]
                }
            return None