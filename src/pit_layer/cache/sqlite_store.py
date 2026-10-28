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
            self._ensure_financial_facts_schema(cursor)
            # Tabelle für Aktiensplits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_splits (
                    ticker TEXT,
                    date TEXT,
                    split_ratio REAL,
                    PRIMARY KEY (ticker, date)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_observations (
                    provider TEXT NOT NULL,
                    series TEXT NOT NULL,
                    observation_date TEXT NOT NULL,
                    available_date TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    PRIMARY KEY (provider, series, observation_date, available_date)
                )
            """)
            conn.commit()

    @staticmethod
    def _ensure_financial_facts_schema(cursor: sqlite3.Cursor) -> None:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_facts (
                ticker TEXT NOT NULL,
                concept TEXT NOT NULL,
                val REAL,
                fy INTEGER,
                fp TEXT,
                start_date TEXT,
                end_date TEXT,
                filed TEXT,
                accepted TEXT,
                form TEXT,
                accession TEXT,
                provider TEXT NOT NULL,
                PRIMARY KEY (ticker, concept, fy, fp, start_date, end_date,
                             accepted, provider)
            )
        """)
        columns = {
            row[1] for row in cursor.execute(
                "PRAGMA table_info(financial_facts)"
            ).fetchall()
        }
        required = {"start_date", "end_date"}
        if required.issubset(columns):
            return

        cursor.execute("ALTER TABLE financial_facts RENAME TO financial_facts_legacy")
        cursor.execute("""
            CREATE TABLE financial_facts (
                ticker TEXT NOT NULL,
                concept TEXT NOT NULL,
                val REAL,
                fy INTEGER,
                fp TEXT,
                start_date TEXT,
                end_date TEXT,
                filed TEXT,
                accepted TEXT,
                form TEXT,
                accession TEXT,
                provider TEXT NOT NULL,
                PRIMARY KEY (ticker, concept, fy, fp, start_date, end_date,
                             accepted, provider)
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO financial_facts
            (ticker, concept, val, fy, fp, start_date, end_date, filed,
             accepted, form, accession, provider)
            SELECT ticker, concept, val, fy, fp, NULL, NULL, filed, accepted,
                   form, accession, provider
            FROM financial_facts_legacy
        """)
        cursor.execute("DROP TABLE financial_facts_legacy")

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
                (ticker, concept, val, fy, fp, start_date, end_date, filed,
                 accepted, form, accession, provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

    def get_pit_value(self, ticker: str, concept: str, year: int, period: str, as_of_date: Optional[str]) -> Optional[dict]:
        # Wir filtern nun primär nach dem exakten accepted-Timestamp für micro-precision PIT
        query = """
            SELECT val, filed, accepted, form, accession, start_date, end_date
            FROM financial_facts
            WHERE ticker = ? AND concept = ? AND fy = ? AND fp = ?
        """
        params = [ticker, concept, year, period]

        if as_of_date:
            if len(as_of_date) == 10:
                as_of_date = f"{as_of_date}T23:59:59"
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
                    "accession": res[4],
                    "start": res[5],
                    "end": res[6],
                }
            return None

    def save_splits(self, records: list):
        """Erwartet eine Liste von Tuples: (ticker, date, split_ratio)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO stock_splits (ticker, date, split_ratio)
                VALUES (?, ?, ?)
            """, records)
            conn.commit()

    def get_splits(self, ticker: str, as_of_date: Optional[str] = None) -> list:
        """Gibt eine Liste von Dicts mit allen Splits eines Tickers zurück."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Absteigend sortiert (neueste Splits zuerst)
            query = "SELECT date, split_ratio FROM stock_splits WHERE ticker = ?"
            params = [ticker]
            if as_of_date:
                query += " AND date <= ?"
                params.append(as_of_date[:10])
            query += " ORDER BY date DESC"
            res = conn.execute(query, params).fetchall()
            return [dict(row) for row in res]

    def save_market_observations(self, records: list) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO market_observations
                (provider, series, observation_date, available_date, value, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

    def get_market_observations(
        self, provider: str, series: str, as_of_date: Optional[str] = None
    ) -> list:
        query = """
            SELECT observation_date, available_date, value, metadata
            FROM market_observations
            WHERE provider = ? AND series = ?
        """
        params = [provider, series]
        if as_of_date:
            query += " AND available_date <= ?"
            params.append(as_of_date)
        query += " ORDER BY observation_date"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(query, params).fetchall()]