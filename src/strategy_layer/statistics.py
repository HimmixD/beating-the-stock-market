from dataclasses import dataclass
import math
import pandas as pd


@dataclass(frozen=True)
class TestResult:
    statistic: float
    p_value: float


class HypothesisTester:
    def sharpe_t_test(self, returns: pd.Series, annualization: int = 252) -> TestResult:
        values = returns.dropna().to_numpy(dtype=float)
        if len(values) < 2:
            raise ValueError("Mindestens zwei Renditen erforderlich.")
        mean, std = values.mean(), values.std(ddof=1)
        if std == 0:
            return TestResult(float("inf") if mean > 0 else 0.0, 0.0 if mean > 0 else 1.0)
        statistic = mean / std * math.sqrt(len(values))
        try:
            from scipy.stats import t
            p_value = float(2 * t.sf(abs(statistic), len(values) - 1))
        except ImportError:
            p_value = float(math.erfc(abs(statistic) / math.sqrt(2)))
        return TestResult(statistic, p_value)

    def walk_forward(self, returns: pd.Series, train_size: int, test_size: int) -> list[TestResult]:
        if train_size <= 0 or test_size <= 0:
            raise ValueError("Fenster müssen positiv sein.")
        results = []
        for start in range(0, len(returns) - train_size - test_size + 1, test_size):
            results.append(self.sharpe_t_test(returns.iloc[start + train_size:start + train_size + test_size]))
        return results
