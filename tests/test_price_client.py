import pytest
import pandas as pd
from pit_layer.clients.price_client import PriceClient

@pytest.fixture
def price_client():
    return PriceClient()

def test_fetch_historical_prices_apple(price_client):
    """Testet, ob historische Kursdaten für Apple geladen werden können."""
    df = price_client.fetch_historical_prices("AAPL", start_date="2023-01-02", end_date="2023-01-31")
    
    assert df is not None, "Keine Kursdaten für Apple erhalten."
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    
    # Prüfen, ob die essenziellen Spalten vorhanden sind
    expected_columns = ["Open", "High", "Low", "Close", "Volume"]
    for col in expected_columns:
        assert col in df.columns, f"Spalte {col} fehlt in den Kursdaten!"

def test_fetch_historical_prices_invalid_ticker(price_client):
    """Testet das Verhalten bei einem ungültigen Ticker."""
    df = price_client.fetch_historical_prices("DIESER_TICKER_EXISTIERT_GARANTIERT_NICHT_123")
    assert df is None, "Sollte bei ungültigem Ticker None zurückgeben."