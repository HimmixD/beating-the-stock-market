from enum import Enum
import pandas as pd


class Regime(str, Enum):
    CRISIS = "crisis"
    GROWTH = "growth"
    NORMAL = "normal"


class RegimeFilter:
    def __init__(self, dxy_window: int = 20, rate_column: str = "DFF"):
        self.dxy_window, self.rate_column = dxy_window, rate_column

    def classify(self, macro: pd.DataFrame) -> pd.Series:
        dxy = macro["DXY"].pct_change(self.dxy_window)
        rates = macro[self.rate_column].diff()
        return pd.Series(Regime.NORMAL.value, index=macro.index).where(
            ~((dxy > 0.05) | (rates > 0.5)), Regime.CRISIS.value
        ).where(~((dxy < -0.05) & (rates <= 0)), Regime.GROWTH.value)

    def is_enabled(self, data: pd.DataFrame) -> pd.Series:
        return self.classify(data).eq(Regime.GROWTH.value) | self.classify(data).eq(Regime.NORMAL.value)
