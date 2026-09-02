from openbb import obb

result = obb.equity.fundamental.cash(
    symbol="AAPL",
    provider="sec",
    period="annual",
    limit=3,
    pit_mode=True,
)

df = result.to_df()

print("\nCOLUMNS:")
for column in df.columns:
    print(repr(column))

print("\nDATA:")
print(df.head(3).to_string())