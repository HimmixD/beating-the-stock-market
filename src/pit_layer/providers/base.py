from abc import ABC, abstractmethod
from typing import Any, Optional
from pit_layer.cache.sqlite_store import SQLiteStore

class BaseProvider(ABC):
    def __init__(self, cache: SQLiteStore):
        self.cache = cache

    @abstractmethod
    def fetch_and_cache(self, ticker: str):
        """Zieht Daten von der API und schreibt sie in den Cache."""
        pass

    @abstractmethod
    def get_value(self, ticker: str, concept: str, year: int, period: str,
                  as_of_date: Optional[str]) -> Optional[Any]:
        """Gibt den PIT-Wert zurück."""
        pass