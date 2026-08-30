from openbb import obb
import pandas as pd


TICKER = "AAPL"


# ============================================================
# 1. GET SEC FILINGS
# ============================================================

print("=" * 80)
print("GETTING SEC FILINGS")
print("=" * 80)

filings = obb.equity.fundamental.filings(
    symbol=TICKER,
    provider="sec",
    limit=200
).to_dataframe()

print("\nFiling columns:")
print(filings.columns.tolist())


# ============================================================
# 2. ONLY FUNDAMENTAL FILINGS
# ============================================================

fundamental_filings = filings[
    filings["report_type"].isin(
        ["10-K", "10-Q", "10-K/A", "10-Q/A"]
    )
].copy()

print("\nFundamental filings:")
print(
    fundamental_filings[
        [
            "filing_date",
            "report_type",
            "report_date",
            "accession_number",
            "accepted_date",
        ]
    ].to_string(index=False)
)


# ============================================================
# 3. GET PIT BALANCE SHEET
# ============================================================

print("\n")
print("=" * 80)
print("GETTING PIT BALANCE SHEET")
print("=" * 80)

balance = obb.equity.fundamental.balance(
    symbol=TICKER,
    provider="sec",
    period="annual",
    limit=20,
    pit_mode=True,
).to_dataframe()

print("\nBalance columns:")
print(balance.columns.tolist())


# ============================================================
# 4. CHECK METADATA
# ============================================================

print("\n")
print("=" * 80)
print("BALANCE METADATA")
print("=" * 80)

metadata_candidates = [
    "filing_date",
    "accepted_date",
    "accession_number",
    "report_date",
    "form",
    "report_type",
]

for column in metadata_candidates:

    if column in balance.columns:

        print(
            f"\nFOUND: {column}"
        )

        print(
            balance[column].head(20).to_string(
                index=False
            )
        )

    else:

        print(
            f"NOT FOUND: {column}"
        )


# ============================================================
# 5. PRINT PERIODS
# ============================================================

print("\n")
print("=" * 80)
print("BALANCE PERIODS")
print("=" * 80)

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
# 6. TRY TO MATCH BY DATE
# ============================================================

print("\n")
print("=" * 80)
print("POSSIBLE FILING MATCHES")
print("=" * 80)

balance["period_ending"] = pd.to_datetime(
    balance["period_ending"],
    errors="coerce"
)

fundamental_filings["report_date"] = pd.to_datetime(
    fundamental_filings["report_date"],
    errors="coerce"
)

for _, row in balance.iterrows():

    period_end = row["period_ending"]

    matches = fundamental_filings[
        fundamental_filings["report_date"]
        == period_end
    ]

    print("\n" + "-" * 80)

    print(
        f"Financial period: {period_end.date()}"
    )

    if matches.empty:

        print(
            "NO EXACT FILING MATCH"
        )

    else:

        print(
            matches[
                [
                    "filing_date",
                    "report_type",
                    "report_date",
                    "accession_number",
                    "accepted_date",
                ]
            ].to_string(index=False)
        )