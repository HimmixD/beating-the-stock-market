from typing import Optional
from pit_layer.providers.base import BaseProvider
from pit_layer.clients.sec_client import SecClient
from pit_layer.utils import SEC_CONCEPT_MAP

class SecProvider(BaseProvider):
    def __init__(self, cache, client: SecClient = None):
        super().__init__(cache)
        self.client = client

    def _client(self) -> SecClient:
        if self.client is None:
            self.client = SecClient()
        return self.client

    def _ensure_cik(self, ticker: str) -> str:
        cik = self.cache.get_cik(ticker)
        if cik:
            return cik
            
        client = self._client()
        tickers_data = client.fetch_tickers()
        for entry in tickers_data.values():
            t = entry["ticker"].upper()
            c = str(entry["cik_str"]).zfill(10)
            self.cache.save_mapping(t, c, "sec")
            if t == ticker:
                cik = c
                
        if not cik:
            raise ValueError(f"Ticker {ticker} bei SEC nicht gefunden.")
        return cik

    def fetch_and_cache(self, ticker: str):
        ticker = ticker.upper()
        cik = self._ensure_cik(ticker)
        facts_data = self._client().fetch_company_facts(cik)
        
        facts = facts_data.get("facts", {}).get("us-gaap", {})
        records = []
        
        for concept, details in facts.items():
            for unit_key, items in details.get("units", {}).items():
                for item in items:
                    form = item.get("form")
                    if form in ["10-K", "10-Q", "10-K/A", "10-Q/A"]:
                        # 1. Fallback für Fiscal Year (fy): Wenn SEC kein fy liefert, nehmen wir das Jahr aus dem 'end'-Datum
                        fy = item.get("fy")
                        if not fy and "end" in item:
                            try:
                                fy = int(item["end"][:4])
                            except (ValueError, TypeError):
                                continue
                        
                        if not fy:
                            continue # Ohne Jahr können wir nichts anfangen

                        # 2. Fallback für Fiscal Period (fp): Bei 10-K ist es immer FY
                        fp = item.get("fp")
                        if not fp:
                            if form in ["10-K", "10-K/A"]:
                                fp = "FY"
                            elif form in ["10-Q", "10-Q/A"]:
                                fp = "Q" # Grobschätzung, falls fp fehlt

                        filed = item.get("filed")
                        if not filed:
                            continue
                        raw_accepted = item.get("accepted", filed + "T23:59:59")
                        accepted_ts = raw_accepted.replace("Z", "").split("+")[0]
                        
                        records.append((
                            ticker,
                            concept,
                            item.get("val"),
                            int(fy),
                            fp,
                            item.get("start"),
                            item.get("end"),
                            filed,
                            accepted_ts,
                            form,
                            item.get("accn"),
                            "sec"
                        ))
                        
        self.cache.save_facts(records)

    def get_value(self, ticker: str, concept: str, year: int, period: str = "FY", as_of_date: Optional[str] = None) -> Optional[dict]:
        ticker = ticker.upper()
        possible_concepts = SEC_CONCEPT_MAP.get(concept.lower(), [concept])
        
        # 1. Cache Check
        for sec_concept in possible_concepts:
            result = self.cache.get_pit_value(ticker, sec_concept, year, period, as_of_date)
            if result is not None:
                return self._enrich_result(result, as_of_date)
                
        # 2. Falls nicht im Cache, Daten laden
        print(f"Lade initial SEC Daten für {ticker}...")
        self.fetch_and_cache(ticker)
        
        # 3. Erneuter Check
        for sec_concept in possible_concepts:
            result = self.cache.get_pit_value(ticker, sec_concept, year, period, as_of_date)
            if result is not None:
                return self._enrich_result(result, as_of_date)
                
        return None

    def _enrich_result(self, result: dict, as_of_date: Optional[str]) -> dict:
        """Fügt den Vertrauens-Tag (PIT Confidence) hinzu."""
        result["pit_status"] = "safe_pit" if as_of_date else "latest_snapshot_warning_lookahead"
        return result