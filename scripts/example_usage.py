from quant.data.provider_bootstrap import build_fundamentals_service

svc = build_fundamentals_service()
a = svc.get_value("AAPL", "revenue", 2017, "income")
b = svc.get_value("AAPL", "revenue", 2017, "income")

print("1st cache_hit:", a.cache_hit)  # expected False
print("2nd cache_hit:", b.cache_hit)  # expected True