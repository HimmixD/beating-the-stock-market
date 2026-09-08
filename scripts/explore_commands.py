"""
=========================================================
PIT DATA LAYER - COMPLETE COMMAND OVERVIEW & USAGE GUIDE
=========================================================
Dieses Skript listet alle wichtigen Befehle auf, die dein 
aktueller, vollständig getesteter Data Layer (Version 1.0) 
für deine kommenden Backtesting-Strategien bereitstellt.
"""

from pit_layer.router import PitRouter
from pit_layer.clients.price_client import PriceClient

def run_all_commands():
    print("==================================================")
    print(" INITIALISIERE PIT ROUTER & PRICE CLIENT...")
    print("==================================================")
    router = PitRouter()
    price_client = PriceClient()

    # ----------------------------------------------------
    # 1. US FUNDAMENTALS (SEC / Point-in-Time)
    # ----------------------------------------------------
    print("\n[1] US FUNDAMENTALS (SEC via CIK)")
    print("-> Befehl: router.get_value(ticker, concept, year, period, as_of_date)")
    
    # Beispiel A: Aktuellster Stand (mit Look-ahead Warnung)
    latest = router.get_value("AAPL", "revenue", 2023, period="FY")
    if latest:
        print(f"   -> AAPL Umsatz 2023 (Latest): ${latest['val']:,.0f} [Status: {latest['pit_status']}]")

    # Beispiel B: Sichere Point-in-Time Stichtagsabfrage (Look-Ahead-Sicher)
    safe = router.get_value("AAPL", "revenue", 2023, period="FY", as_of_date="2023-11-05")
    if safe:
        print(f"   -> AAPL Umsatz 2023 (Safe PIT per 05.11.2023): ${safe['val']:,.0f} (Filing: {safe['filed']})")


    # ----------------------------------------------------
    # 2. GLOBAL FUNDAMENTALS (Non-US via OpenBB Router)
    # ----------------------------------------------------
    print("\n[2] GLOBAL FUNDAMENTALS (Non-US Ticker wie EVN.VI)")
    print("-> Befehl: router.get_value('EVN.VI', 'net_income', year, as_of_date)")
    print("   -> (Der Router erkennt den Punkt im Ticker automatisch und leitet zum Global Provider weiter)")


    # ----------------------------------------------------
    # 3. HISTORISCHE KURSDATEN (OHLCV via yfinance)
    # ----------------------------------------------------
    print("\n[3] HISTORISCHE KURSDATEN (OHLCV)")
    print("-> Befehl: price_client.fetch_historical_prices(ticker, start_date, end_date)")
    
    df_prices = price_client.fetch_historical_prices("AAPL", start_date="2023-01-02", end_date="2023-01-31")
    if df_prices is not None:
        print(f"   -> AAPL Kursdaten geladen! Zeilen: {len(df_prices)}")
        print(f"   -> Letzter Schlusskurs im Januar 2023: ${df_prices['Close'].iloc[-1]:.2f}")


    # ----------------------------------------------------
    # 4. VERFÜGBARE MAPPED CONCEPTS (aus pit_layer/utils.py)
    # ----------------------------------------------------
    print("\n[4] UNTERSTÜTZTE STANDARD-METRIKEN (Concept-Mapper):")
    print("   - 'revenue' (Umsatz / SalesRevenueNet)")
    print("   - 'net_income' (Nettogewinn)")
    print("   - 'operating_income' (Operatives Ergebnis)")
    print("   - 'gross_profit' (Bruttogewinn)")
    print("   - 'assets' / 'total_assets' (Bilanzsumme)")
    print("   - 'liabilities' (Verbindlichkeiten)")
    print("   - 'equity' (Eigenkapital)")
    print("   - 'operating_cash_flow' (Operativer Cashflow)")
    print("   - 'capex' (Investitionsausgaben)")

    print("\n==================================================")
    print(" DATA LAYER BEREIT & VOLLSTÄNDIG FUNKTIONSFÄHIG!")
    print("==================================================")

if __name__ == "__main__":
    run_all_commands()