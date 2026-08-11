import yfinance as yf
import pandas as pd
import datetime as dt

ticker = yf.Ticker("AAPL")

# Get historical market data
hist = ticker.history(start="2020-01-01", end=dt.datetime.now().strftime("%Y-%m-%d"))
hist_raw = ticker.history(start="2020-01-01", end="2021-01-05", auto_adjust=False)

hist["momentum_252d"] = hist["Close"].pct_change(periods=252)
hist["future_return_20d"] = hist["Close"].shift(-20).pct_change(periods=20)



# Output the historical data
#print(hist["Close"].pct_change().describe())
#print(hist.loc["2020"])

#print(hist["Close"].mean())
#print(hist["Volume"].mean())
#print(hist["Close"].min())
#print(hist["Close"].max())

start_price = hist.loc["2020-01-02", "Close"]
future_price = hist.iloc[20]["Close"]
print(f"Start price: {start_price}")
print(f"Future price: {future_price}")
print(f"Future return: {future_price / start_price -1:.2%}")
print(hist.loc["2020-01-02", "future_return_20d"])

#hist.to_csv("data/raw/AAPL_price.csv")