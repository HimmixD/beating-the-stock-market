from openbb import obb
import pandas as pd


TICKER = "AAPL"


# ============================================================
# GET QUARTERLY PIT BALANCE
# ============================================================

print("=" * 80)
print("QUARTERLY PIT BALANCE")
print("=" * 80)

balance = obb.equity.fundamental.balance(
    symbol=TICKER,
    provider="sec",
    period="quarterly",
    limit=40,
    pit_mode=True,
).to_dataframe()


print("\nColumns:")
print(balance.columns.tolist())


print("\nShape:")
print(balance.shape)


print("\nQuarterly data:")
print(
    balance[
        [
            "period_ending",
            "fiscal_period",
            "fiscal_year",
            "total_assets",
            "total_liabilities",
            "total_equity",
        ]
    ].to_string(index=False)
)


# ============================================================
# GET QUARTERLY NORMAL
# ============================================================

normal = obb.equity.fundamental.balance(
    symbol=TICKER,
    provider="sec",
    period="quarterly",
    limit=40,
    pit_mode=False,
).to_dataframe()


print("\n")
print("=" * 80)
print("PIT vs NORMAL QUARTERLY")
print("=" * 80)


pit = balance.copy()
norm = normal.copy()


pit["period_ending"] = pd.to_datetime(
    pit["period_ending"]
)

norm["period_ending"] = pd.to_datetime(
    norm["period_ending"]
)


comparison = pd.merge(
    pit[
        [
            "period_ending",
            "total_assets",
            "total_liabilities",
            "total_equity",
        ]
    ],
    norm[
        [
            "period_ending",
            "total_assets",
            "total_liabilities",
            "total_equity",
        ]
    ],
    on="period_ending",
    suffixes=("_pit", "_normal"),
)


comparison["assets_diff"] = (
    comparison["total_assets_pit"]
    - comparison["total_assets_normal"]
)

comparison["liabilities_diff"] = (
    comparison["total_liabilities_pit"]
    - comparison["total_liabilities_normal"]
)

comparison["equity_diff"] = (
    comparison["total_equity_pit"]
    - comparison["total_equity_normal"]
)


print(
    comparison.to_string(index=False)
)


print("\n")
print("=" * 80)
print("ACTUAL DIFFERENCES")
print("=" * 80)


differences = comparison[
    (
        comparison["assets_diff"].abs()
        > 0
    )
    |
    (
        comparison["liabilities_diff"].abs()
        > 0
    )
    |
    (
        comparison["equity_diff"].abs()
        > 0
    )
]


print(
    differences.to_string(index=False)
)