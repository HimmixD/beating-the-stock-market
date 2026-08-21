import yfinance as yf
import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 500)

ticker_dic = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "Financials": ["JPM", "BAC", "GS", "V", "MA"],
    "Consumer": ["AMZN", "WMT", "KO", "MCD"],
    "Communication": ["DIS", "NFLX"],
    "Industrials": ["CAT", "GE", "HON"],
    "Health Care": ["JNJ", "PFE", "MOH", "UNH", "ABBV"],
    "Energy": ["XOM", "CVX", "COP"]
}

momentum = [20, 60, 126, 252]
future_return = [5, 20, 60, 126]

def get_stock_data(ticker, sector, momentum, future_return):
    'Get stock data for a given ticker and sector from Yahoo Finance.'

    df = yf.download(
        ticker,
        period="max",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    # MultiIndex bei yfinance entfernen
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["ticker"] = ticker
    df["sector"] = sector

    for momentum_period in momentum:
        df[f"momentum_{momentum_period}d"] = df["Close"].pct_change(momentum_period)

    for future_return_period in future_return:
        df[f"future_return_{future_return_period}d"] = (
            df["Close"].shift(-future_return_period) / df["Close"] - 1
        )

    return df


# running all stocks in the ticker dictionary and saving them in a list, which will be concatenated into a single DataFrame
all_data = []

for sector, tickers in ticker_dic.items():
    for ticker in tickers:
        for momentum_period in momentum:
            for future_return_period in future_return:
                print(f"Loading {ticker} with Momentum Period {momentum_period} and Future Return Period {future_return_period}...")

                df = get_stock_data(ticker, sector, momentum, future_return)

                all_data.append(df)

data = pd.concat(all_data)

data = data.reset_index()

data.head()

print(data)