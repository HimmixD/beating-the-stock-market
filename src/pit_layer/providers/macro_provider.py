"""Cached, point-in-time macroeconomic data access."""

from __future__ import annotations

import csv
import io
import json
import os
from typing import Callable, Iterable, Optional
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
import yfinance as yf

from pit_layer.cache.sqlite_store import SQLiteStore


class MacroProvider:
    """Fetches FRED series and DXY, retaining the first available vintage."""

    def __init__(
        self,
        cache: SQLiteStore,
        fred_api_key: Optional[str] = None,
        fred_fetcher: Optional[Callable[[str], Iterable[dict]]] = None,
        dxy_fetcher: Optional[Callable[[], pd.DataFrame]] = None,
    ):
        self.cache = cache
        self.fred_api_key = fred_api_key or os.getenv("FRED_API_KEY")
        self._fred_fetcher = fred_fetcher or self._fetch_fred
        self._dxy_fetcher = dxy_fetcher or self._fetch_dxy

    def fetch_and_cache(self, series_id: str) -> None:
        records = []
        for row in self._fred_fetcher(series_id):
            observation_date = str(row["observation_date"])[:10]
            available_date = str(row.get("realtime_start", observation_date))[:10]
            value = row.get("value")
            if value in (None, ".", ""):
                continue
            records.append(("fred", series_id.upper(), observation_date,
                            available_date, float(value), json.dumps({"source": "FRED"})))
        if records:
            self.cache.save_market_observations(records)

    def fetch_dxy_and_cache(self, start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> None:
        frame = self._dxy_fetcher()
        if frame is None or frame.empty:
            raise RuntimeError("DXY lieferte keine Daten.")
        values = frame["Close"] if "Close" in frame else frame.iloc[:, 0]
        records = []
        for timestamp, value in values.dropna().items():
            observation_date = pd.Timestamp(timestamp).strftime("%Y-%m-%d")
            if start_date and observation_date < start_date:
                continue
            if end_date and observation_date >= end_date:
                continue
            records.append(("yfinance", "DXY", observation_date, observation_date,
                            float(value), json.dumps({"ticker": "DX-Y.NYB"})))
        if records:
            self.cache.save_market_observations(records)

    def get_series(self, series_id: str, as_of_date: Optional[str] = None) -> pd.Series:
        rows = self.cache.get_market_observations("fred", series_id.upper(), as_of_date)
        if not rows:
            self.fetch_and_cache(series_id)
            rows = self.cache.get_market_observations("fred", series_id.upper(), as_of_date)
        return pd.Series(
            {pd.Timestamp(row["observation_date"]): row["value"] for row in rows},
            dtype="float64",
            name=series_id.upper(),
        ).sort_index()

    def get_dxy(self, as_of_date: Optional[str] = None) -> pd.Series:
        rows = self.cache.get_market_observations("yfinance", "DXY", as_of_date)
        if not rows:
            self.fetch_dxy_and_cache()
            rows = self.cache.get_market_observations("yfinance", "DXY", as_of_date)
        return pd.Series(
            {pd.Timestamp(row["observation_date"]): row["value"] for row in rows},
            dtype="float64",
            name="DXY",
        ).sort_index()

    def get_features(self, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """Return standard macro features; missing FRED series remain absent."""
        series = {}
        for series_id in ("DFF", "CPIAUCSL"):
            series[series_id] = self.get_series(series_id, as_of_date)
        series["DXY"] = self.get_dxy(as_of_date)
        return pd.concat(series, axis=1).sort_index()

    def _fetch_fred(self, series_id: str) -> Iterable[dict]:
        if self.fred_api_key:
            query = urlencode({"series_id": series_id, "api_key": self.fred_api_key,
                               "file_type": "json", "sort_order": "asc"})
            with urlopen("https://api.stlouisfed.org/fred/series/observations?" + query,
                         timeout=30) as response:
                return json.load(response)["observations"]
        with urlopen(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?"
            + urlencode({"id": series_id}), timeout=30
        ) as response:
            return list(csv.DictReader(io.TextIOWrapper(response, encoding="utf-8")))

    @staticmethod
    def _fetch_dxy() -> pd.DataFrame:
        return yf.download("DX-Y.NYB", period="max", progress=False, auto_adjust=True)
