"""
OpenBB Quant Data Diagnostic
============================

Ziel:
    OpenBB als Daten-Layer für ein Point-in-Time Quant Research Projekt testen.

    Wir untersuchen insbesondere:
    - historische Preise
    - Fundamentals
    - Filing-/Publication-Dates
    - historische Perioden
    - Provider
    - US vs. internationale Aktien
    - Datenqualität

    WICHTIG:
    Dieser Test beweist NICHT, dass ein Provider Point-in-Time-safe ist.
    Er zeigt uns lediglich, ob die dafür benötigten Informationen vorhanden sind.

Installation:
    pip install openbb

Optional:
    Weitere Provider müssen ggf. separat installiert/configuriert werden.
"""

from datetime import datetime
import traceback

from openbb import obb


# ============================================================
# CONFIG
# ============================================================

TEST_TICKERS = {
    "US": [
        "AAPL",
        "MSFT",
        "NVDA",
    ],
    "EU": [
        "SAP",
        "ASML",
    ],
}

START_DATE = "2018-01-01"
END_DATE = "2026-08-01"

# Manche OpenBB-Versionen/Provider verwenden andere Namen.
# Deshalb testen wir mehrere mögliche Provider.
PROVIDERS_TO_TEST = [
    None,       # OpenBB Default
    "yfinance",
    "sec",
    "fmp",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_dataframe_info(df, name, max_rows=5):
    """
    Zeigt grundlegende Informationen über ein DataFrame.
    """
    if df is None:
        print(f"{name}: None")
        return

    print(f"\n--- {name} ---")

    print("Shape:", df.shape)

    print("\nColumns:")
    for column in df.columns:
        print(f"  - {column}")

    print("\nDtypes:")
    print(df.dtypes)

    print("\nFirst rows:")
    print(df.head(max_rows))

    print("\nLast rows:")
    print(df.tail(max_rows))


def safe_call(description, function):
    """
    Führt einen OpenBB-Call aus, ohne dass das gesamte Programm
    bei einem Provider-Fehler abstürzt.
    """

    print(f"\n>>> {description}")

    try:
        result = function()

        print("SUCCESS")

        # OpenBB liefert normalerweise ein OBBject.
        print("Result type:", type(result))

        try:
            df = result.to_dataframe()

            print_dataframe_info(
                df,
                description
            )

            return result, df

        except Exception as e:
            print("Konnte Result nicht in DataFrame umwandeln.")
            print("Fehler:", e)
            print("Raw result:")
            print(result)

            return result, None

    except Exception as e:
        print("FAILED")
        print("Error:", repr(e))

        return None, None


# ============================================================
# 1. OPENBB INSTALLATION / BASIC TEST
# ============================================================

print_header("1. OPENBB BASIC TEST")

print("OpenBB object:")
print(obb)

print("\nOpenBB type:")
print(type(obb))


# ============================================================
# 2. PROVIDER TEST
# ============================================================

print_header("2. PROVIDER TEST")

print("""
Wir versuchen verschiedene Provider.

Ein Fehler bei einem Provider ist kein Problem.
Wir wollen gerade herausfinden, welche Provider verfügbar sind.
""")

for provider in PROVIDERS_TO_TEST:

    provider_name = provider if provider else "DEFAULT"

    print("\n" + "-" * 60)
    print("Provider:", provider_name)
    print("-" * 60)

    try:

        if provider is None:

            result = obb.equity.price.historical(
                "AAPL",
                start_date=START_DATE,
                end_date=END_DATE,
            )

        else:

            result = obb.equity.price.historical(
                "AAPL",
                start_date=START_DATE,
                end_date=END_DATE,
                provider=provider,
            )

        df = result.to_dataframe()

        print("SUCCESS")
        print("Rows:", len(df))
        print("Columns:", list(df.columns))

        print(df.head())

    except Exception as e:

        print("FAILED")
        print("Reason:", repr(e))


# ============================================================
# 3. HISTORICAL PRICE DATA
# ============================================================

print_header("3. HISTORICAL PRICE TEST")

for ticker in TEST_TICKERS["US"] + TEST_TICKERS["EU"]:

    safe_call(
        f"{ticker} historical prices",
        lambda ticker=ticker: obb.equity.price.historical(
            ticker,
            start_date=START_DATE,
            end_date=END_DATE,
        ),
    )


# ============================================================
# 4. COMPANY PROFILE
# ============================================================

print_header("4. COMPANY PROFILE TEST")

for ticker in TEST_TICKERS["US"] + TEST_TICKERS["EU"]:

    safe_call(
        f"{ticker} company profile",
        lambda ticker=ticker: obb.equity.profile(
            ticker
        ),
    )


# ============================================================
# 5. INCOME STATEMENT
# ============================================================

print_header("5. INCOME STATEMENT TEST")

for ticker in TEST_TICKERS["US"]:

    safe_call(
        f"{ticker} income statement",
        lambda ticker=ticker: obb.equity.fundamental.income(
            ticker
        ),
    )


# ============================================================
# 6. BALANCE SHEET
# ============================================================

print_header("6. BALANCE SHEET TEST")

for ticker in TEST_TICKERS["US"]:

    safe_call(
        f"{ticker} balance sheet",
        lambda ticker=ticker: obb.equity.fundamental.balance(
            ticker
        ),
    )


# ============================================================
# 7. CASH FLOW
# ============================================================

print_header("7. CASH FLOW TEST")

for ticker in TEST_TICKERS["US"]:

    safe_call(
        f"{ticker} cash flow",
        lambda ticker=ticker: obb.equity.fundamental.cash(
            ticker
        ),
    )


# ============================================================
# 8. EARNINGS
# ============================================================

print_header("8. EARNINGS TEST")

for ticker in TEST_TICKERS["US"]:

    safe_call(
        f"{ticker} earnings",
        lambda ticker=ticker: obb.equity.earnings(
            ticker
        ),
    )


# ============================================================
# 9. SEC TEST
# ============================================================

print_header("9. SEC TEST")

for ticker in TEST_TICKERS["US"]:

    safe_call(
        f"{ticker} SEC filings",
        lambda ticker=ticker: obb.equity.fundamental.filing(
            ticker
        ),
    )


# ============================================================
# 10. DEEP POINT-IN-TIME INSPECTION
# ============================================================

print_header("10. POINT-IN-TIME FIELD INSPECTION")

ticker = "AAPL"

result, df = safe_call(
    f"{ticker} detailed income statement",
    lambda: obb.equity.fundamental.income(
        ticker
    ),
)

if df is not None:

    print("\nALL COLUMNS:")
    print(list(df.columns))

    print("\nPOSSIBLE DATE COLUMNS:")

    date_keywords = [
        "date",
        "time",
        "period",
        "ending",
        "filing",
        "publish",
        "reported",
        "accepted",
        "updated",
    ]

    for column in df.columns:

        column_lower = column.lower()

        if any(
            keyword in column_lower
            for keyword in date_keywords
        ):

            print("\nCOLUMN:", column)

            try:
                print(df[column].head(20))
            except Exception:
                pass


# ============================================================
# 11. LOOK FOR FILING / PUBLICATION INFORMATION
# ============================================================

print_header("11. FILING / PUBLICATION DATE SEARCH")

if df is not None:

    possible_columns = []

    for column in df.columns:

        name = column.lower()

        if any(
            keyword in name
            for keyword in [
                "filing",
                "publish",
                "accepted",
                "reported",
                "date",
                "period",
            ]
        ):

            possible_columns.append(column)

    print("Potentially relevant columns:")

    for column in possible_columns:
        print("  ", column)


# ============================================================
# 12. HISTORICAL PERIOD TEST
# ============================================================

print_header("12. HISTORICAL PERIOD TEST")

print("""
Wir wollen wissen:

Bekommen wir tatsächlich mehrere historische Perioden?

Oder bekommen wir lediglich den aktuellsten Datensatz
mit alten period_end Dates?
""")

result, df = safe_call(
    "AAPL historical income data",
    lambda: obb.equity.fundamental.income(
        "AAPL"
    ),
)

if df is not None:

    print("\nNumber of rows:", len(df))

    print("\nPotential period columns:")

    for column in df.columns:

        name = column.lower()

        if "period" in name or "date" in name or "ending" in name:

            print("\n", column)

            try:
                print(df[column].drop_duplicates().head(30))
            except Exception:
                pass


# ============================================================
# 13. INTERNATIONAL TEST
# ============================================================

print_header("13. INTERNATIONAL EQUITY TEST")

international_tickers = [
    "SAP",
    "ASML",
    "NESN.SW",
    "MC.PA",
]

for ticker in international_tickers:

    safe_call(
        f"{ticker} historical prices",
        lambda ticker=ticker: obb.equity.price.historical(
            ticker,
            start_date=START_DATE,
            end_date=END_DATE,
        ),
    )


# ============================================================
# 14. PROVIDER COMPARISON
# ============================================================

print_header("14. PROVIDER COMPARISON")

ticker = "AAPL"

provider_results = {}

for provider in [
    "yfinance",
    "fmp",
    "sec",
]:

    print("\n" + "-" * 60)
    print(provider)
    print("-" * 60)

    try:

        result = obb.equity.fundamental.income(
            ticker,
            provider=provider,
        )

        df = result.to_dataframe()

        provider_results[provider] = df

        print("Rows:", len(df))
        print("Columns:")
        print(list(df.columns))

        print("\nFirst rows:")
        print(df.head())

    except Exception as e:

        print("FAILED:", repr(e))


# ============================================================
# 15. COMPARE COLUMN STRUCTURE
# ============================================================

print_header("15. PROVIDER COLUMN COMPARISON")

for provider, df in provider_results.items():

    print("\n", provider)

    print(set(df.columns))


# ============================================================
# 16. DATA REVISION WARNING
# ============================================================

print_header("16. LOOK-AHEAD / REVISION WARNING")

print("""
IMPORTANT:

Dieser Test kann NICHT beweisen, dass die gelieferten
Fundamentaldaten point-in-time korrekt sind.

Wir müssen insbesondere prüfen:

1. Gibt es ein Filing Date?
2. Gibt es ein Accepted Date?
3. Gibt es ein Publication Date?
4. Gibt es Period End?
5. Werden alte Werte nachträglich überschrieben?
6. Können mehrere Versionen desselben Fundamentals existieren?
7. Können wir den Datensatz anhand des Veröffentlichungsdatums
   rekonstruieren?

Wenn diese Informationen fehlen, ist der Datensatz für einen
strengen Point-in-Time Backtest möglicherweise ungeeignet.
""")


# ============================================================
# 17. FINAL SUMMARY
# ============================================================

print_header("17. TEST FINISHED")

print("""
OpenBB diagnostic completed.

Bitte speichere die komplette Terminal-Ausgabe.

Besonders interessant sind:

- verfügbare Provider
- Income Statement columns
- Balance Sheet columns
- Cash Flow columns
- Earnings columns
- SEC columns
- Filing / publication dates
- period ending dates
- Unterschiede zwischen Providern
- Verhalten bei SAP / ASML

Der nächste Schritt ist NICHT automatisch ROIC.

Wir müssen zuerst feststellen, ob wir aus diesen Daten
einen echten Point-in-Time Fundamental Datensatz bauen können.
""")