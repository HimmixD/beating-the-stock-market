from datetime import datetime, timezone
from quant.data.provider_bootstrap import build_fundamentals_service

def test_non_us_fallback_is_tagged():
    svc = build_fundamentals_service()
    res = svc.get_value(
        symbol="NESN.SW",
        field="revenue",
        fiscal_year=2023,
        statement="income",
        as_of_date=datetime(2024, 3, 1, tzinfo=timezone.utc),
        use_cache=False,
    )
    fv = res.financial_value
    assert fv.provider == "global_openbb"
    assert fv.source == "openbb"
    assert fv.pit_status == "provider_claimed"