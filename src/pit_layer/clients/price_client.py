import yfinance as yf
import pandas as pd
from typing import Optional

class PriceClient:
    def __init__(self):
        pass

    def fetch_historical_prices(self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Holt historische OHLCV-Kursdaten (Open, High, Low, Close, Volume) für einen Ticker via yfinance.
        """
        try:
            # progress=False unterdrückt die Ladebalken im Terminal
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df is None or df.empty:
                return None
                
            # Manchmal liefert yfinance einen MultiIndex bei den Spalten in neueren Versionen. 
            # Wir bereinigen das, falls nötig, damit der Zugriff einfach bleibt.
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            return df
        except Exception as e:
            print(f"Fehler beim Abrufen der Kursdaten für {ticker}: {e}")
            return None