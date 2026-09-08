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
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            
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

    def fetch_splits(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Holt historische Aktiensplits für einen Ticker via yfinance.
        Gibt ein leeres DataFrame zurück, falls es keine Splits gab.
        """
        try:
            splits = yf.Ticker(ticker).splits
            if splits.empty:
                return pd.DataFrame()
                
            df = splits.reset_index()
            # yfinance liefert datetime-Objekte, wir brauchen saubere ISO-Strings
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            df.rename(columns={'Date': 'date', 'Stock Splits': 'split_ratio'}, inplace=True)
            return df
        except Exception as e:
            print(f"Fehler beim Abrufen der Splits für {ticker}: {e}")
            return None