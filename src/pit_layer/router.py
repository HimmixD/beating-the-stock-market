from typing import Optional
from pit_layer.cache.sqlite_store import SQLiteStore
from pit_layer.providers.sec_provider import SecProvider
from pit_layer.providers.global_provider import GlobalProvider

class PitRouter:
    def __init__(self):
        self.cache = SQLiteStore()
        self.sec_provider = SecProvider(self.cache)
        self.global_provider = GlobalProvider(self.cache)

    def _is_us_ticker(self, ticker: str) -> bool:
        # US-Ticker haben in der Regel keinen Punkt (kein Börsenkürzel wie .VI oder .DE)
        return "." not in ticker

    def get_value(self, ticker: str, concept: str, year: int, period: str = "FY", as_of_date: Optional[str] = None) -> Optional[dict]:
        if self._is_us_ticker(ticker):
            return self.sec_provider.get_value(ticker, concept, year, period, as_of_date)
        else:
            return self.global_provider.get_value(ticker, concept, year, period, as_of_date)