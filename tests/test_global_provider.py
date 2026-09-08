import pytest
from pit_layer.cache.sqlite_store import SQLiteStore
from pit_layer.providers.global_provider import GlobalProvider

class MockOpenBBClient:
    """Mock-Client, der strukturierte OpenBB-Daten simuliert, ohne das Internet zu belasten."""
    def fetch_fundamentals(self, ticker: str, statement_type: str = "income"):
        if statement_type == "income":
            return [
                {
                    "date": "2023-12-31",
                    "NetIncome": 150000000.0,
                    "TotalRevenue": 500000000.0
                }
            ]
        return []

def test_global_provider_saving_and_retrieval(tmp_path):
    """Testet, ob der GlobalProvider Daten korrekt mit 10 Bindings in den Cache schreibt und ausliest."""
    # Wir nutzen ein temporäres Dateipfad-Objekt von pytest für diesen Test
    db_file = tmp_path / "test_database.db"
    store = SQLiteStore(db_path=str(db_file))
    
    mock_client = MockOpenBBClient()
    provider = GlobalProvider(cache=store, client=mock_client)
    
    ticker = "TEST.VI"
    
    # Trigger fetch_and_cache via Mock
    provider.fetch_and_cache(ticker)
    
    # Versuchen den Wert abzurufen
    result = provider.get_value(ticker, "NetIncome", 2023, period="FY")
    
    assert result is not None, "GlobalProvider konnte den gecachten Wert nicht abrufen!"
    assert result["val"] == 150000000.0
    assert result["form"] == "ANNUAL"