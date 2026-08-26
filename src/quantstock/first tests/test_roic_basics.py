#general imports
import pandas as pd
import numpy as np
import yfinance as yf

#options
pd.set_option('display.max_rows', 500)

#-------------------------------------------------

# defining the tickers
ticker_dic = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "Financials": ["JPM", "BAC", "GS", "V", "MA"],
    "Consumer": ["AMZN", "WMT", "KO", "MCD"],
    "Communication": ["DIS", "NFLX"],
    "Industrials": ["CAT", "GE", "HON"],
    "Health Care": ["JNJ", "PFE", "MOH", "UNH", "ABBV"],
    "Energy": ["XOM", "CVX", "COP"]
}
ticker = yf.Ticker("DKS")



financials = ticker.financials
balance_sheet = ticker.balance_sheet


print(financials)
print(balance_sheet)
