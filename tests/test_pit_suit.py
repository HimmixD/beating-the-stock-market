import pytest
from pit_layer.router import PitRouter

@pytest.fixture
def router():
    return PitRouter()

def test_router_routing_logic(router):
    """Testet, ob der Router korrekt zwischen SEC (US) und Global (Non-US) unterscheidet."""
    assert router._is_us_ticker("AAPL") is True
    assert router._is_us_ticker("MSFT") is True
    assert router._is_us_ticker("EVN.VI") is False
    assert router._is_us_ticker("BMW.DE") is False

def test_sec_provider_apple_revenue(router):
    """Testet den US-Standard (SEC) anhand von Apple."""
    data = router.get_value("AAPL", "revenue", 2023, period="FY")
    
    assert data is not None, "Keine Daten für Apple 2023 gefunden."
    assert "val" in data
    assert data["val"] > 300_000_000_000  # Apple Umsatz 2023 war > 300 Mrd.
    assert data["pit_status"] == "latest_snapshot_warning_lookahead"

def test_pit_time_travel_constraints(router):
    """Testet die Point-in-Time Stichtagslogik (verhindert Look-Ahead-Bias)."""
    # Vor dem offiziellen Filing-Datum im Herbst 2023 darf kein Wert da sein
    data_past = router.get_value("AAPL", "revenue", 2023, period="FY", as_of_date="2023-10-01")
    assert data_past is None, "Look-Ahead-Fehler: Daten aus der Zukunft wurden akzeptiert!"

    # Nach dem Filing-Datum muss der Wert da und als safe markiert sein
    data_present = router.get_value("AAPL", "revenue", 2023, period="FY", as_of_date="2023-12-01")
    assert data_present is not None
    assert data_present["pit_status"] == "safe_pit"

def test_global_provider_routing(router):
    """Testet, ob der Global Router für Non-US Ticker anspringt (mit Fallback-Check)."""
    # Wir testen hier den Aufruf für EVN.VI. 
    # Da yfinance bei internationalen Werten oft limitiert ist, fangen wir Fehler/None sauber ab.
    try:
        data = router.get_value("EVN.VI", "net_income", 2020)
        # Wenn Daten kommen, prüfen wir die Struktur
        if data is not None:
            assert "val" in data
            assert "pit_status" in data
    except Exception as e:
        pytest.fail(f"Test, dass Global Router abstürzt statt None zurückzugeben: {e}")