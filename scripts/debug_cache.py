import sqlite3

db = sqlite3.connect(".cache/fundamentals.sqlite")
rows = db.execute("""
SELECT provider, symbol, field, fiscal_year, fiscal_period, fiscal_period_key, value
FROM financial_values
ORDER BY symbol, field, fiscal_year
""").fetchall()

print("ROWS:", len(rows))
for r in rows[:50]:
    print(r)