import pandas as pd

from pit_layer.cache.sqlite_store import SQLiteStore
from pit_layer.providers.macro_provider import MacroProvider


def test_fred_cache_is_point_in_time(tmp_path):
    cache = SQLiteStore(str(tmp_path / "cache.db"))
    provider = MacroProvider(cache, fred_fetcher=lambda _: [
        {"observation_date": "2020-01-01", "realtime_start": "2020-02-01", "value": "1.0"},
        {"observation_date": "2020-02-01", "realtime_start": "2020-03-01", "value": "2.0"},
    ])

    assert provider.get_series("DFF", "2020-02-15").tolist() == [1.0]
    assert provider.get_series("DFF", "2020-03-01").tolist() == [1.0, 2.0]


def test_dxy_is_cached_and_filtered(tmp_path):
    cache = SQLiteStore(str(tmp_path / "cache.db"))
    frame = pd.DataFrame({"Close": [100.0, 101.0]},
                         index=pd.to_datetime(["2020-01-01", "2020-01-02"]))
    provider = MacroProvider(cache, dxy_fetcher=lambda: frame,
                             fred_fetcher=lambda _: [])

    assert provider.get_dxy("2020-01-01").tolist() == [100.0]
