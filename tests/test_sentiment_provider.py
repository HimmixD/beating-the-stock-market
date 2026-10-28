import pandas as pd

from pit_layer.cache.sqlite_store import SQLiteStore
from pit_layer.providers.sentiment_provider import SentimentProvider


def test_sentiment_score_and_news_cache(tmp_path):
    cache = SQLiteStore(str(tmp_path / "cache.db"))
    provider = SentimentProvider(
        cache,
        news_fetcher=lambda _: [
            {"content": {"title": "Strong growth and profit", "pubDate": "2024-01-02T10:00:00Z"}}
        ],
    )

    assert provider.score("Strong growth and profit") == 1.0
    feature = provider.get_feature("AAPL", "2024-01-02")
    assert feature.index.equals(pd.DatetimeIndex(["2024-01-02"]))
    assert feature.iloc[0] == 1.0
