from datetime import datetime, timezone
from quant.data.provider_bootstrap import build_fundamentals_service

svc = build_fundamentals_service()

res = svc.get_value(
    symbol="AMZN",
    field="total_assets",
    fiscal_year=2008,
    fiscal_period="FY",
    as_of_date=datetime(2009, 3, 28, tzinfo=timezone.utc),
)

print("RESULT:", res)