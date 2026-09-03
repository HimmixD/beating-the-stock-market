from datetime import datetime, timezone
from quant.data.provider_bootstrap import build_fundamentals_service

svc = build_fundamentals_service()

res = svc.get_value(
    symbol="JPM",
    field="total_assets",
    fiscal_year=2008,
    statement="balance",
    fiscal_period="FY",
    as_of_date=datetime(2018, 1, 1, tzinfo=timezone.utc),
)

print("RESULT:", res)