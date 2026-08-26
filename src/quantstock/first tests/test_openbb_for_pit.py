from openbb import obb
import inspect

print(inspect.signature(obb.equity.fundamental.income))
print(inspect.signature(obb.equity.fundamental.balance))
print(inspect.signature(obb.equity.fundamental.cash))
print(inspect.signature(obb.equity.fundamental.income_growth))

income = obb.equity.fundamental.income(
    symbol="AAPL",
    provider="sec",
    period="annual",
    limit=20,
    pit_mode=True,
)

df = income.to_dataframe()

print(df.columns)
print(df)

income_normal = obb.equity.fundamental.income(
    symbol="AAPL",
    provider="sec",
    period="annual",
    limit=20,
    pit_mode=False,
)

df_normal = income_normal.to_dataframe()

print(df_normal)