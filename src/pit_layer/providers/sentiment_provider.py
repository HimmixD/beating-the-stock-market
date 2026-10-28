"""News sentiment features with a deterministic baseline scorer."""

from __future__ import annotations

import re
from typing import Callable, Optional

import pandas as pd
import yfinance as yf

from pit_layer.cache.sqlite_store import SQLiteStore


class SentimentProvider:
    POSITIVE = frozenset({"beat", "growth", "gain", "upgrade", "strong", "profit", "surge"})
    NEGATIVE = frozenset({"miss", "loss", "downgrade", "weak", "risk", "fall", "crisis"})

    def __init__(self, cache: SQLiteStore,
                 news_fetcher: Optional[Callable[[str], list]] = None):
        self.cache = cache
        self._news_fetcher = news_fetcher or (lambda ticker: yf.Ticker(ticker).news or [])

    def fetch_and_cache(self, ticker: str) -> None:
        records = []
        for article in self._news_fetcher(ticker):
            content = article.get("content", article)
            title = content.get("title", "") if isinstance(content, dict) else ""
            published = content.get("pubDate", content.get("providerPublishTime", ""))
            timestamp = pd.to_datetime(published, unit="s", errors="coerce")
            if pd.isna(timestamp):
                timestamp = pd.to_datetime(published, errors="coerce")
            if pd.isna(timestamp) or not title:
                continue
            day = timestamp.strftime("%Y-%m-%d")
            records.append(("sentiment", ticker.upper(), day, day,
                            self.score(title), '{"title": true}'))
        if records:
            self.cache.save_market_observations(records)

    def score(self, text: str) -> float:
        tokens = set(re.findall(r"[a-z]+", text.lower()))
        positive = len(tokens & self.POSITIVE)
        negative = len(tokens & self.NEGATIVE)
        return (positive - negative) / max(1, positive + negative)

    def get_feature(self, ticker: str, as_of_date: Optional[str] = None) -> pd.Series:
        rows = self.cache.get_market_observations("sentiment", ticker.upper(), as_of_date)
        if not rows:
            self.fetch_and_cache(ticker)
            rows = self.cache.get_market_observations("sentiment", ticker.upper(), as_of_date)
        return pd.Series({pd.Timestamp(r["observation_date"]): r["value"] for r in rows},
                         dtype="float64", name=f"{ticker.upper()}_sentiment").sort_index()
