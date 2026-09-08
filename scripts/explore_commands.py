"""
=========================================================
PIT DATA LAYER - COMMAND OVERVIEW & USAGE GUIDE
=========================================================
Dieses Skript dient als kompakte Übersicht und Test-Umgebung 
für alle zentralen Befehle, die dir für deine Backtesting-
Strategien jetzt zur Verfügung stehen.
"""

from pit_layer.router import PitRouter
from pit_layer.clients.price_client import PriceClient

def run_overview():
    print("==================================================")
    print(" INITIALISIERE PIT ROUTER & CLIENTS...")
    print("==================================================")
    router = PitRouter()
    price_client = PriceClient()

    # ----------------------------------------------------
    # 1. US FUNDAMENTALS (Point-in-Time über SEC)
    # ----------------------------------------------------
    print("\n[1] US FUNDAMENTALS (SEC / Point-in-Time)")
    print("-> Befehl: router.get_value(ticker, concept, year, period, as_of_date)")
    
    # Beispiel A: Aktuellster Stand (mit Look-ahead Warnung)
    latest_rev = router.get_value("AAPL", "revenue", 2023, period="FY")
    print(f"   -> AAPL Umsatz 2023 (Latest): ${latest_rev['val']:,.0f} [Status: {latest_rev['pit_status']}]")

    # Beispiel B: Sichere Point-in-Time Abfrage (Stichtagsbezogen ohne Look-ahead Bias)
    safe_rev = router.get_value("AAPL", "revenue", 2023, period="FY", as_of_date="2023-11-05")
    print(f"   -> AAPL Umsatz 2023 (Safe PIT per 05.11.2023): ${safe_rev['val']:,.0f} (Filing-Datum: {safe_rev['filed']})")


    # ----------------------------------------------------
    # 2. GLOBAL FUNDAMENTALS (Non-US via OpenBB Router)
    # ----------------------------------------------------
    print("\n[2] GLOBAL FUNDAMENTALS (Non-US Ticker)")
    print("-> Befehl: router.get_value('EVN.VI', 'net_income', year)")
    print("   -> (Leitet automatisch an den Global Provider weiter, wenn ein Punkt im Ticker ist)")
    # Hinweis: EVN.VI oder andere internationale Ticker je nach Datenverfügbarkeit


    # ----------------------------------------------------
    # 3. HISTORISCHE KURSDATEN (OHLCV für Momentum etc.)
    # ----------------------------------------------------
    print("\n[3] HISTORISCHE KURSDATEN (yfinance Price Client)")
    print("-> Befehl: price_client.fetch_historical_prices(ticker, start_date, end_date)")
    
    df_prices = price_client.fetch_historical_prices("AAPL", start_date="2023-01-02", end_date="2023-01-31")
    if df_prices is not None:
        print(f"   -> AAPL Kursdaten erfolgreich geladen! Zeilen: {len(df_prices)}")
        print(f"   -> Letzter Schlusskurs im Januar 2023: ${df_prices['Close'].iloc[-1]:.2f}")


    # ----------------------------------------------------
    # 4. VERFÜGBARE FINANZ-METRIKEN (MAPPING BIBLIOTHEK)
    # ----------------------------------------------------
    print("\n[4] VERFÜGBARE MAPPED CONCEPTS (aus pit_layer/utils.py)")
    print("   Du kannst folgende vereinfachte Begriffe in deinen Skripten nutzen:")
    print("   - 'revenue' (Umsatz)")
    print("   - 'net_income' (Nettogewinn)")
    print("   - 'operating_income' (Operatives Ergebnis)")
    print("   - 'gross_profit' (Bruttogewinn)")
    print("   - 'assets' / 'total_assets' (Bilanzsumme / Vermögen)")
    print("   - 'liabilities' (Verbindlichkeiten)")
    print("   - 'equity' (Eigenkapital)")
    print("   - 'operating_cash_flow' (Cashflow aus operativer Tätigkeit)")
    print("   - 'capex' (Investitionsausgaben)")

    print("\n==================================================")
    print(" ALLES BEREIT FÜR DEINE STRATEGIEN!")
    print("==================================================")

if __name__ == "__main__":
    run_overview()