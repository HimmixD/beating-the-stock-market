from datetime import datetime, timezone
from quant.data.cache_store import FinancialValueCache
from quant.data.models import FinancialValue
from datetime import date


def _fv(val: float):
    return FinancialValue(
        symbol="TEST",
        field="revenue",
        value=val,
        currency="USD",
        period_end=date(2020, 12, 31),
        fiscal_year=2020,
        fiscal_period="FY",
        filing_date=date(2021, 2, 1),
        accepted_date=datetime(2021, 2, 1, 12, 0, tzinfo=timezone.utc),
        provider="sec",
        source="sec_fact",
        pit_status="authoritative",
        confidence=1.0,
    )


def test_cache_is_asof_isolated(tmp_path):
    db = tmp_path / "fundamentals.sqlite"
    cache = FinancialValueCache(str(db))

    a1 = datetime(2021, 2, 1, 12, 0, tzinfo=timezone.utc)
    a2 = datetime(2021, 3, 1, 12, 0, tzinfo=timezone.utc)

    cache.put(_fv(100.0), as_of_date=a1)
    cache.put(_fv(110.0), as_of_date=a2)

    r1 = cache.get("sec", "TEST", "revenue", 2020, "FY", a1)
    r2 = cache.get("sec", "TEST", "revenue", 2020, "FY", a2)

    assert r1 is not None and r1.value == 100.0
    assert r2 is not None and r2.value == 110.0