from openbb import obb
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

TICKER = "AAPL"
LIMIT = 30

OUTPUT_DIR = Path("pit_test_output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# HELPER
# ============================================================

def get_data(endpoint_name, pit_mode):
    """
    Ruft einen OpenBB-SEC-Fundamental-Endpoint ab.
    """

    print(
        f"\nFetching {endpoint_name} | "
        f"pit_mode={pit_mode}"
    )

    try:

        if endpoint_name == "balance":
            result = obb.equity.fundamental.balance(
                symbol=TICKER,
                provider="sec",
                period="quarterly",
                limit=LIMIT,
                pit_mode=pit_mode,
            )

        elif endpoint_name == "income":
            result = obb.equity.fundamental.income(
                symbol=TICKER,
                provider="sec",
                period="quarterly",
                limit=LIMIT,
                pit_mode=pit_mode,
            )

        elif endpoint_name == "cash":
            result = obb.equity.fundamental.cash(
                symbol=TICKER,
                provider="sec",
                period="quarterly",
                limit=LIMIT,
                pit_mode=pit_mode,
            )

        else:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")

        df = result.to_dataframe()

        return df

    except Exception as e:

        print(f"ERROR: {e}")

        return pd.DataFrame()


# ============================================================
# DISPLAY
# ============================================================

def inspect_dataframe(df, name):

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    if df.empty:
        print("NO DATA")
        return

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst rows:")
    print(df.head())

    print("\nData types:")
    print(df.dtypes)


# ============================================================
# CHECK PIT METADATA
# ============================================================

def check_pit_metadata(df):

    print("\n" + "=" * 80)
    print("PIT METADATA CHECK")
    print("=" * 80)

    if df.empty:
        return

    important_columns = [
        "symbol",
        "period_ending",
        "filing_date",
        "accepted_date",
        "fiscal_year",
        "fiscal_period",
    ]

    available = [
        c for c in important_columns
        if c in df.columns
    ]

    print("\nAvailable PIT-related columns:")
    print(available)

    if "filing_date" not in df.columns:

        print(
            "\nWARNING: filing_date is missing."
            "\nThis would be a serious problem for our PIT system."
        )

        return

    df = df.copy()

    df["period_ending"] = pd.to_datetime(
        df["period_ending"],
        errors="coerce"
    )

    df["filing_date"] = pd.to_datetime(
        df["filing_date"],
        errors="coerce"
    )

    df["accepted_date"] = pd.to_datetime(
        df["accepted_date"],
        errors="coerce"
    )

    print("\nRelevant data:")

    cols = [
        c for c in [
            "symbol",
            "period_ending",
            "filing_date",
            "accepted_date",
            "fiscal_year",
            "fiscal_period",
        ]
        if c in df.columns
    ]

    print(
        df[cols]
        .sort_values("filing_date")
        .to_string(index=False)
    )

    # Filing date should normally be >= period end
    invalid = df[
        df["filing_date"].notna()
        & df["period_ending"].notna()
        & (df["filing_date"] < df["period_ending"])
    ]

    print("\nInvalid filing dates:")

    if invalid.empty:
        print("NONE")
    else:
        print(invalid[cols].to_string(index=False))


# ============================================================
# COMPARE PIT VS NON-PIT
# ============================================================

def compare_pit_vs_normal(pit_df, normal_df):

    print("\n" + "=" * 80)
    print("PIT vs NON-PIT")
    print("=" * 80)

    if pit_df.empty or normal_df.empty:
        print("Cannot compare.")
        return

    print(
        f"\nPIT rows:    {len(pit_df)}"
    )

    print(
        f"Normal rows: {len(normal_df)}"
    )

    if "period_ending" not in pit_df.columns:
        print("period_ending missing.")
        return

    if "period_ending" not in normal_df.columns:
        print("period_ending missing.")
        return

    pit = pit_df.copy()
    normal = normal_df.copy()

    pit["period_ending"] = pd.to_datetime(
        pit["period_ending"],
        errors="coerce"
    )

    normal["period_ending"] = pd.to_datetime(
        normal["period_ending"],
        errors="coerce"
    )

    # Find columns that exist in both datasets
    common_columns = [
        c for c in pit.columns
        if c in normal.columns
    ]

    # Focus on important financial values
    financial_columns = [
        "total_assets",
        "total_liabilities",
        "total_equity",
        "cash_and_cash_equivalents",
        "total_debt",
        "revenue",
        "net_income",
        "operating_income",
        "net_cash_from_operating_activities",
        "free_cash_flow",
    ]

    comparison_columns = [
        c for c in financial_columns
        if c in common_columns
    ]

    if not comparison_columns:

        print(
            "\nNo common financial columns found "
            "for comparison."
        )

        return

    merged = pd.merge(
        pit[
            ["period_ending"] + comparison_columns
        ],
        normal[
            ["period_ending"] + comparison_columns
        ],
        on="period_ending",
        how="outer",
        suffixes=("_pit", "_normal"),
    )

    print("\nComparison:")

    for column in comparison_columns:

        pit_col = f"{column}_pit"
        normal_col = f"{column}_normal"

        if (
            pit_col not in merged.columns
            or normal_col not in merged.columns
        ):
            continue

        merged[f"{column}_difference"] = (
            merged[pit_col] -
            merged[normal_col]
        )

    print(
        merged
        .sort_values("period_ending")
        .to_string(index=False)
    )

    return merged


# ============================================================
# HISTORICAL KNOWLEDGE TEST
# ============================================================

def historical_knowledge_test(df, test_date):

    print("\n" + "=" * 80)
    print(
        f"HISTORICAL KNOWLEDGE TEST: {test_date}"
    )
    print("=" * 80)

    if df.empty:
        return

    if "filing_date" not in df.columns:
        print("filing_date missing.")
        return

    df = df.copy()

    df["filing_date"] = pd.to_datetime(
        df["filing_date"],
        errors="coerce"
    )

    test_date = pd.Timestamp(test_date)

    # Only information that had been filed by the test date
    available = df[
        df["filing_date"] <= test_date
    ].copy()

    print(
        f"\nTotal observations: {len(df)}"
    )

    print(
        f"Observations available on {test_date.date()}: "
        f"{len(available)}"
    )

    if available.empty:
        print("No financial information available.")
        return

    cols = [
        c for c in [
            "period_ending",
            "filing_date",
            "fiscal_year",
            "fiscal_period",
        ]
        if c in available.columns
    ]

    print(
        available
        .sort_values("filing_date")
        [cols]
        .to_string(index=False)
    )

    print(
        "\nThis is the basic mechanism our future "
        "backtester will use."
    )


# ============================================================
# SAVE
# ============================================================

def save_data(df, filename):

    if df.empty:
        return

    path = OUTPUT_DIR / filename

    df.to_csv(
        path,
        index=False
    )

    print(
        f"\nSaved: {path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 80)
    print("OPENBB SEC POINT-IN-TIME TEST")
    print("=" * 80)
    print(f"Ticker: {TICKER}")
    print("=" * 80)


    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    balance_pit = get_data(
        "balance",
        pit_mode=True
    )

    balance_normal = get_data(
        "balance",
        pit_mode=False
    )

    inspect_dataframe(
        balance_pit,
        "BALANCE - PIT"
    )

    check_pit_metadata(
        balance_pit
    )

    compare_pit_vs_normal(
        balance_pit,
        balance_normal
    )

    save_data(
        balance_pit,
        "AAPL_balance_pit.csv"
    )

    save_data(
        balance_normal,
        "AAPL_balance_normal.csv"
    )


    # --------------------------------------------------------
    # INCOME
    # --------------------------------------------------------

    income_pit = get_data(
        "income",
        pit_mode=True
    )

    income_normal = get_data(
        "income",
        pit_mode=False
    )

    inspect_dataframe(
        income_pit,
        "INCOME - PIT"
    )

    check_pit_metadata(
        income_pit
    )

    compare_pit_vs_normal(
        income_pit,
        income_normal
    )

    save_data(
        income_pit,
        "AAPL_income_pit.csv"
    )

    save_data(
        income_normal,
        "AAPL_income_normal.csv"
    )


    # --------------------------------------------------------
    # CASH FLOW
    # --------------------------------------------------------

    cash_pit = get_data(
        "cash",
        pit_mode=True
    )

    cash_normal = get_data(
        "cash",
        pit_mode=False
    )

    inspect_dataframe(
        cash_pit,
        "CASH FLOW - PIT"
    )

    check_pit_metadata(
        cash_pit
    )

    compare_pit_vs_normal(
        cash_pit,
        cash_normal
    )

    save_data(
        cash_pit,
        "AAPL_cash_pit.csv"
    )

    save_data(
        cash_normal,
        "AAPL_cash_normal.csv"
    )


    # --------------------------------------------------------
    # HISTORICAL KNOWLEDGE TEST
    # --------------------------------------------------------

    historical_knowledge_test(
        balance_pit,
        "2021-06-01"
    )

    historical_knowledge_test(
        income_pit,
        "2021-06-01"
    )

    historical_knowledge_test(
        cash_pit,
        "2021-06-01"
    )


    print("\n")
    print("=" * 80)
    print("TEST FINISHED")
    print("=" * 80)

    print(
        "\nCheck the generated files in:"
    )

    print(
        OUTPUT_DIR.resolve()
    )


if __name__ == "__main__":
    main()



from openbb import obb
import pandas as pd


print("\n")
print("=" * 80)
print("SEC FILINGS TEST")
print("=" * 80)

filings = obb.equity.fundamental.filings(
    symbol="AAPL",
    provider="sec",
    limit=30
)

filings_df = filings.to_dataframe()

print("\nColumns:")
print(filings_df.columns.tolist())

print("\nData:")
print(filings_df.to_string(index=False))