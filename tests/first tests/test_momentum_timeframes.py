import yfinance as yf
import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 500)

reload_data = False  # Set to True to reload data from Yahoo Finance, False to load from CSV

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

def get_stock_data(ticker, sector):
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
if reload_data:
    all_data = []

    for sector, tickers in ticker_dic.items():
        for ticker in tickers:
            print(f"Loading {ticker} ...")

            df = get_stock_data(ticker, sector)

            all_data.append(df)

    data = pd.concat(all_data)

    data = data.reset_index()

    data.head()

    #save the data to a CSV file
    data.to_csv("data/raw/momentum_data_25082026.csv")

data = pd.read_csv("data/raw/momentum_data_25082026.csv", index_col=0)


results = []

for momentum_period in momentum:

    momentum_col = f"momentum_{momentum_period}d"

    # Quantile pro Aktie
    quantile_col = f"{momentum_col}_quantile"

    data[quantile_col] = (
        data
        .groupby("ticker")[momentum_col]
        .transform(
            lambda x: pd.qcut(
                x,
                q=5,
                labels=False,
                duplicates="drop"
            ) + 1
        )
    )

    for future_return_period in future_return:

        future_col = f"future_return_{future_return_period}d"

        # Nur gültige Beobachtungen verwenden
        temp = data.dropna(
            subset=[
                momentum_col,
                future_col,
                quantile_col
            ]
        )

        quantile_analysis = (
            temp
            .groupby(quantile_col)[future_col]
            .agg(
                mean_return="mean",
                median_return="median",
                count="count"
            )
            .reset_index()
        )

        q1 = quantile_analysis.loc[
            quantile_analysis[quantile_col] == 1,
            "mean_return"
        ].iloc[0]

        q5 = quantile_analysis.loc[
            quantile_analysis[quantile_col] == 5,
            "mean_return"
        ].iloc[0]

        results.append({
            "momentum": momentum_period,
            "future_return": future_return_period,
            "Q5 - Q1": q5 - q1
        })

results_df = pd.DataFrame(results)

print(results_df)



stock_results = []

for ticker, group in data.groupby("ticker"):

    q1 = group.loc[
        group["momentum_126d_quantile"] == 1,
        "future_return_126d"
    ].mean()

    q5 = group.loc[
        group["momentum_126d_quantile"] == 5,
        "future_return_126d"
    ].mean()

    stock_results.append({
        "ticker": ticker,
        "Q1": q1,
        "Q5": q5,
        "Q5-Q1": q5 - q1
    })

stock_results = pd.DataFrame(stock_results)

print(stock_results)
print(stock_results["Q5-Q1"].describe())
print((stock_results["Q5-Q1"] > 0).mean())

