import pytest
from pit_layer.router import PitRouter

@pytest.fixture
def router():
    return PitRouter()

def test_router_apple_revenue(router):
    """Testet, ob Apple-Umsatz für 2023 korrekt geladen wird."""
    data = router.get_value("AAPL", "revenue", 2023, period="FY")
    
    assert data is not None, "Keine Daten für Apple 2023 gefunden"
    assert "val" in data
    assert "pit_status" in data
    assert data["val"] > 300_000_000_000, "unvollständig" # Apple Umsatz 2023 war > 380 Mrd.
    assert data["pit_status"] == "latest_snapshot_warning_lookahead"

def test_pit_time_travel(router):
    """Testet echtes Point-in-Time (Stichtags-Abfrage in der Vergangenheit)."""
    # Apple hat das 2023er 10-K im November 2023 eingereicht. 
    # Wenn wir als_of_date auf den 01.10.2023 setzen, darf das 2023er FY noch NICHT da sein!
    data_past = router.get_value("AAPL", "revenue", 2023, period="FY", as_of_date="2023-10-01")
    assert data_past is None, "Look-ahead-Fehler! Daten aus der Zukunft wurden geladen."

    # Wenn wir das as_of_date auf Dezember 2023 setzen, muss es da sein.
    data_present = router.get_value("AAPL", "revenue", 2023, period="FY", as_of_date="2023-12-01")
    assert data_present is not None
    assert data_present["pit_status"] == "safe_pit"