import pandas as pd
from typing import Optional
from pit_layer.providers.base import BaseProvider
from pit_layer.clients.openbb_client import OpenBBClient

class GlobalProvider(BaseProvider):
    def __init__(self, cache, client: OpenBBClient = None):
        super().__init__(cache)
        try:
            self.client = client or OpenBBClient()
        except ImportError:
            self.client = None

    def fetch_and_cache(self, ticker: str):
        if not self.client:
            raise RuntimeError("OpenBB Client ist nicht verfügbar.")
            
        ticker = ticker.upper()
        
        for stmt_type in ["income", "balance", "cash"]:
            records_raw = self.client.fetch_fundamentals(ticker, stmt_type)
            if not records_raw:
                continue
                
            records = []
            for row in records_raw:
                filed_date = self._publication_date(row)
                if filed_date is None:
                    continue
                period_end = self._date_value(row.get("period_ending", row.get("date")))
                period_start = self._date_value(row.get("period_start", row.get("start")))
                try:
                    fy = int((period_end or filed_date)[:4])
                except (ValueError, TypeError):
                    fy = 2023 # Fallback
                
                for col, val in row.items():
                    if col in ["date", "period_ending", "fiscal_year", "period"]:
                        continue
                    if isinstance(val, (int, float)) and pd.notna(val):
                        # The publication date is the PIT availability boundary.
                        records.append((
                            ticker,
                            col,
                            float(val),
                            fy,
                            "FY",
                            period_start,
                            period_end,
                            filed_date,
                            filed_date,
                            "ANNUAL",
                            None,
                            "global_openbb",
                        ))
                        
            if records:
                self.cache.save_facts(records)

    def get_value(self, ticker: str, concept: str, year: int, period: str = "FY", as_of_date: Optional[str] = None) -> Optional[dict]:
        ticker = ticker.upper()
        
        result = self.cache.get_pit_value(ticker, concept, year, period, as_of_date)
        if result is not None:
            return self._enrich_result(result, as_of_date)
            
        print(f"Lade initial Global/OpenBB Daten für {ticker}...")
        try:
            self.fetch_and_cache(ticker)
        except Exception as exc:
            raise RuntimeError(
                f"Global-Daten für {ticker} konnten nicht geladen werden."
            ) from exc
            
        result = self.cache.get_pit_value(ticker, concept, year, period, as_of_date)
        if result is not None:
            return self._enrich_result(result, as_of_date)
            
        return None

    def _enrich_result(self, result: dict, as_of_date: Optional[str]) -> dict:
        result["pit_status"] = "safe_pit" if as_of_date else "latest_snapshot_warning_lookahead"
        return result

    @staticmethod
    def _date_value(value) -> Optional[str]:
        if value is None or pd.isna(value):
            return None
        parsed = pd.to_datetime(value, errors="coerce")
        return None if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")

    def _publication_date(self, row: dict) -> Optional[str]:
        for key in ("filing_date", "filingDate", "published", "publication_date",
                    "report_date"):
            parsed = self._date_value(row.get(key))
            if parsed:
                return parsed
        return None