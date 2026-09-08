import pytest
from pit_layer.router import PitRouter

@pytest.fixture
def router():
    return PitRouter()

def test_apple_stock_splits(router):
    """Testet, ob die historischen Splits von Apple korrekt geladen und gecached werden."""
    splits = router.get_splits("AAPL")
    
    assert splits is not None, "Die Split-Abfrage darf nicht None sein."
    assert len(splits) >= 5, "Apple hatte in der Historie mindestens 5 Splits."
    
    # Prüfe den 4:1 Split im August 2020
    split_2020 = next((s for s in splits if s["date"] == "2020-08-31"), None)
    assert split_2020 is not None, "Der Split vom 31.08.2020 wurde nicht gefunden."
    assert split_2020["split_ratio"] == 4.0, "Der Split-Ratio für 2020 muss 4.0 sein."

    # Prüfe den 7:1 Split im Juni 2014
    split_2014 = next((s for s in splits if s["date"] == "2014-06-09"), None)
    assert split_2014 is not None, "Der Split vom 09.06.2014 wurde nicht gefunden."
    assert split_2014["split_ratio"] == 7.0, "Der Split-Ratio für 2014 muss 7.0 sein."

def test_no_split_stock(router):
    """Testet das Verhalten bei einer Aktie ohne historische Splits (z.B. Berkshire Hathaway A)."""
    splits = router.get_splits("BRK-A")
    assert isinstance(splits, list), "Muss eine Liste zurückgeben."
    assert len(splits) == 0, "BRK-A sollte keine Splits haben."