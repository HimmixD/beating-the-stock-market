import numpy as np
import pandas as pd


class OvernightEffectStrategy:
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        return pd.Series(1.0, index=data.index)


class StatArbStrategy:
    def __init__(self, other_close: pd.Series, lookback: int = 60,
                 entry_z: float = 2.0):
        self.other_close, self.lookback, self.entry_z = other_close, lookback, entry_z

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        spread = np.log(data["Close"]).reindex(self.other_close.index) - np.log(self.other_close)
        z = (spread - spread.rolling(self.lookback).mean()) / spread.rolling(self.lookback).std()
        return (-np.sign(z)).where(z.abs() >= self.entry_z, 0.0).reindex(data.index).fillna(0.0)


class NoiseBandStrategy:
    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window, self.num_std = window, num_std

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        mean = data["Close"].rolling(self.window).mean()
        band = data["Close"].rolling(self.window).std() * self.num_std
        return pd.Series(np.where(data["Close"] > mean + band, 1.0,
                                  np.where(data["Close"] < mean - band, -1.0, 0.0)),
                         index=data.index)
