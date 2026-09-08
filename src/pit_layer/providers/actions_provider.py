from typing import List, Dict
import pandas as pd
from pit_layer.clients.price_client import PriceClient

class ActionsProvider:
    def __init__(self, cache, client: PriceClient = None):
        self.cache = cache
        self.client = client or PriceClient()
        # Verhindert ständige API-Calls für Aktien, die noch nie einen Split hatten
        self._fetched_tickers = set() 

    def fetch_and_cache(self, ticker: str):
        ticker = ticker.upper()
        splits_df = self.client.fetch_splits(ticker)
        
        if splits_df is not None and not splits_df.empty:
            records = [
                (ticker, row['date'], float(row['split_ratio'])) 
                for _, row in splits_df.iterrows()
            ]
            self.cache.save_splits(records)
            
        self._fetched_tickers.add(ticker)

    def get_splits(self, ticker: str) -> List[Dict[str, float]]:
        ticker = ticker.upper()
        splits = self.cache.get_splits(ticker)
        
        # Wenn wir keine Splits in der DB haben UND diesen Ticker in der Session noch nicht geprüft haben -> Fetch!
        if not splits and ticker not in self._fetched_tickers:
            print(f"Prüfe initial auf Split-Daten für {ticker}...")
            self.fetch_and_cache(ticker)
            splits = self.cache.get_splits(ticker)
            
        return splits