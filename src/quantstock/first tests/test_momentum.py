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


def get_stock_data(ticker, sector,):
    'Get stock data for a given ticker and sector from Yahoo Finance.'

    df = yf.download(
        ticker,
        period="max",
        auto_adjust=False,
        progress=False
    )

    # MultiIndex bei yfinance entfernen
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Close"]].copy()

    # 252-Tage-Momentum
    df["momentum_252d"] = df["Close"].pct_change(252)

    # zukünftige 20-Tage-Rendite
    df["future_return_20d"] = (
        df["Close"].shift(-20) / df["Close"] - 1
    )

    df["ticker"] = ticker
    df["sector"] = sector

    return df


# running all stocks in the ticker dictionary and saving them in a list, which will be concatenated into a single DataFrame
all_data = []

for sector, tickers in ticker_dic.items():
    for ticker in tickers:

        print(f"Lade {ticker}...")

        df = get_stock_data(ticker, sector)

        all_data.append(df)


data = pd.concat(all_data)

data = data.reset_index()

data.head()


# setting quantiles for momentum_252d and dropping rows with NaN values
data["momentum_quantile"] = (
    data
    .groupby("ticker")["momentum_252d"]
    .transform(
        lambda x: pd.qcut(
            x,
            q=5,
            labels=False,
            duplicates="drop"
        ) + 1
    )
)
'1 = lowest momentum, 5 = highest momentum'

data = data.dropna(
    subset=[
        "momentum_252d",
        "future_return_20d",
        "momentum_quantile"
    ]
)


# calculating mean, median, and count of future_return_20d for each momentum quantile over all stocks and dates (whole market)
quantile_analysis = (
    data
    .groupby("momentum_quantile")["future_return_20d"]
    .agg(
        mean_return="mean",
        median_return="median",
        count="count"
    )
    .reset_index()
)
quantile_analysis["excess_vs_q1"] = quantile_analysis["mean_return"] - quantile_analysis.loc[0, "mean_return"]


# calculating mean, median, and count of future_return_20d for each momentum quantile for each seperate stock (ticker)
ticker_quantile_analysis = (
    data
    .groupby(["ticker", "momentum_quantile"])["future_return_20d"]
    .agg(
        mean_return="mean",
        median_return="median",
        count="count"
    )
    .reset_index()
)
ticker_quantile_analysis["excess_vs_q1"] = (
    ticker_quantile_analysis
    .groupby("ticker")["mean_return"]
    .transform(lambda x: x - x.iloc[0])
)


# Output the quantile analysis
print(ticker_quantile_analysis)






# analyzing different momentum/future return periods
momentum = [20, 60, 126, 252]
future_return = [5, 20, 60, 126]







