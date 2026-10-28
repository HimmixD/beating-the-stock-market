from pit_layer.router import PitRouter

router = PitRouter()
# Beispiel OMV an der Wiener Börse (falls über OpenBB/yfinance verfügbar)
value = router.get_value("OMV.VI", "net_income", 2023)
print(value)