from typing import Optional
from pit_layer.cache.sqlite_store import SQLiteStore
from pit_layer.providers.sec_provider import SecProvider
from pit_layer.providers.global_provider import GlobalProvider
from pit_layer.providers.actions_provider import ActionsProvider

class PitRouter:
    def __init__(self):
        self.cache = SQLiteStore()
        self.sec_provider = SecProvider(self.cache)
        self.global_provider = GlobalProvider(self.cache)
        self.actions_provider = ActionsProvider(self.cache)

    def _is_us_ticker(self, ticker: str) -> bool:
        # Enhanced routing: check known international exchange suffixes first
        international_suffixes = [".VI", ".DE", ".TO", ".L", ".PA", ".SA", ".MC", ".IS", ".SW"]
        if any(ticker.endswith(s) for s in international_suffixes):
            return False
        # Check for dot in ticker (traditional heuristic)
        if "." in ticker:
            return False
        # Default to US ticker
        return True

    def get_value(self, ticker: str, concept: str, year: int, period: str = "FY", as_of_date: Optional[str] = None) -> Optional[dict]:
        if self._is_us_ticker(ticker):
            return self.sec_provider.get_value(ticker, concept, year, period, as_of_date)
        else:
            return self.global_provider.get_value(ticker, concept, year, period, as_of_date)

    def get_splits(self, ticker: str) -> list:
        """Gibt eine Liste aller historischen Splits eines Tickers zurück."""
        return self.actions_provider.get_splits(ticker)