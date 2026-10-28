from typing import List, Dict
from pit_layer.clients.price_client import PriceClient

class ActionsProvider:
    def __init__(self, cache, client: PriceClient = None):
        self.cache = cache
        self.client = client or PriceClient()
        # Track fetched tickers to avoid unnecessary API calls,
        # but allow refresh when needed
        self._fetched_tickers = set()

    def fetch_and_cache(self, ticker: str, force: bool = False) -> None:
        """Fetch splits for a ticker and cache them.

        Args:
            ticker: Stock ticker symbol
            force: If True, fetches even if ticker was already fetched
        """
        ticker = ticker.upper()

        # Only skip fetch if not force and ticker was already fetched
        if not force and ticker in self._fetched_tickers:
            # Still check cache in case data exists
            splits = self.cache.get_splits(ticker)
            if splits:
                return

        splits_df = self.client.fetch_splits(ticker)

        if splits_df is not None and not splits_df.empty:
            records = [
                (ticker, row['date'], float(row['split_ratio']))
                for _, row in splits_df.iterrows()
            ]
            self.cache.save_splits(records)
            self._fetched_tickers.add(ticker)
        elif force:
            # Even with force, if no data available, mark as fetched
            # to avoid repeated failed attempts
            self._fetched_tickers.add(ticker)

    def get_splits(self, ticker: str, as_of_date: str = None) -> List[Dict[str, float]]:
        ticker = ticker.upper()
        splits = self.cache.get_splits(ticker, as_of_date)

        # If no splits in cache, fetch regardless of _fetched_tickers
        # This ensures we can get data even if previously marked
        if not splits:
            print(f"PrÃ¼fe Split-Daten fÃ¼r {ticker}...")
            self.fetch_and_cache(ticker, force=True)
            splits = self.cache.get_splits(ticker, as_of_date)

        return splits
