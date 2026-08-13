import yfinance as yf
import pandas as pd
import datetime as dt


# define functions
def get_avg_per_quantile(df, sorting_col, target_col, num_quantiles):
    sorted_df = df.sort_values(by=sorting_col)

    sorted_df["quantile"] = pd.qcut(
        sorted_df[sorting_col],
        q=num_quantiles,
        labels=False
    )

    return sorted_df.groupby("quantile")[target_col].mean()



# in progress testing

ticker = yf.Ticker("AAPL")

# Get historical market data
hist = ticker.history(
    start="2020-01-01", 
    end=dt.datetime.now().strftime("%Y-%m-%d")
    )

hist_raw = ticker.history(
    start="2020-01-01", 
    end="2021-01-05", 
    auto_adjust=False
    )

hist["momentum_252d"] = hist["Close"].pct_change(periods=252)
hist["future_return_20d"] = hist["Close"].pct_change(periods=20).shift(-20)
hist.dropna(inplace=True)               #drop rows with NaN values and replace original hist with the new one

momentum_252d = hist["momentum_252d"]
future_return_20d = hist["future_return_20d"]

hist_sorted_by_momentum = hist.sort_values(
    by="momentum_252d", 
    ascending=True
    )

quant = get_avg_per_quantile(hist, "momentum_252d", "future_return_20d", 5)
print(quant)

#hist.to_csv("data/raw/AAPL_price.csv")