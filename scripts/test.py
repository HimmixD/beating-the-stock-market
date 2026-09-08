from pit_layer.router import PitRouter

router = PitRouter()
# Beispiel OMV an der Wiener Börse (falls über OpenBB/yfinance verfügbar)
value = router.get_value("AAPL", "capex", 2022, as_of_date="2022-10-29")
print(value)