from pit_layer.router import PitRouter

router = PitRouter()
# Scratch: Apple capex query for a historical as-of date
value = router.get_value("AAPL", "capex", 2022, as_of_date="2022-10-29")
print(value)
