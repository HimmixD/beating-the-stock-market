import pandas as pd
from typing import Optional, List, Dict, Any

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False

class OpenBBClient:
    def __init__(self, default_provider: str = "yfinance"):
        if not OPENBB_AVAILABLE:
            raise ImportError("OpenBB ist nicht installiert.")
        self.default_provider = default_provider

    def fetch_fundamentals(self, ticker: str, statement_type: str = "income", provider: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Holt Fundamentaldaten über OpenBB für globale Ticker.
        """
        prov = provider or self.default_provider
        try:
            if statement_type == "income":
                data = obb.equity.fundamental.income(symbol=ticker, provider=prov)
            elif statement_type == "balance":
                data = obb.equity.fundamental.balance(symbol=ticker, provider=prov)
            elif statement_type == "cash":
                data = obb.equity.fundamental.cash(symbol=ticker, provider=prov)
            else:
                return None

            df = data.to_df()
            if df is None or df.empty:
                return None
                
            df = df.reset_index()
            return df.to_dict(orient="records")
            
        except Exception as e:
            print(f"OpenBB Fehler bei {ticker} ({statement_type}) mit Provider {prov}: {e}")
            return None