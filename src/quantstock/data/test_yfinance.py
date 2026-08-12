import yfinance as yf
import pandas as pd
import datetime as dt

ticker = yf.Ticker("AAPL")

# Get historical market data
hist = ticker.history(start="2020-01-01", end=dt.datetime.now().strftime("%Y-%m-%d"))
hist_raw = ticker.history(start="2020-01-01", end="2021-01-05", auto_adjust=False)

hist["momentum_252d"] = hist["Close"].pct_change(periods=252)
hist["future_return_20d"] = hist["Close"].pct_change(periods=20).shift(-20)

hist.dropna(inplace=True)



# Output the historical data
#print(hist["Close"].pct_change().describe())
#print(hist.loc["2020"])

#print(hist["Close"].mean())
#print(hist["Volume"].mean())
#print(hist["Close"].min())
#print(hist["Close"].max())
print(hist)

hist.to_csv("data/raw/AAPL_price.csv")