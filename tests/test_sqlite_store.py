from pit_layer.cache.sqlite_store import SQLiteStore


def test_financial_fact_periods_do_not_overwrite_each_other(tmp_path):
    store = SQLiteStore(str(tmp_path / "cache.db"))
    store.save_facts([
        ("TEST", "Revenue", 100.0, 2024, "FY", None, "2024-06-30",
         "2024-08-01", "2024-08-01T23:59:59", "10-K", "a", "sec"),
        ("TEST", "Revenue", 200.0, 2024, "FY", "2024-01-01", "2024-12-31",
         "2025-02-01", "2025-02-01T23:59:59", "10-K", "b", "sec"),
    ])

    first = store.get_pit_value("TEST", "Revenue", 2024, "FY", "2024-12-01")
    second = store.get_pit_value("TEST", "Revenue", 2024, "FY", "2025-03-01")
    assert first["val"] == 100.0
    assert second["val"] == 200.0


def test_same_day_filing_is_available_at_end_of_day(tmp_path):
    store = SQLiteStore(str(tmp_path / "cache.db"))
    store.save_facts([
        ("TEST", "Revenue", 100.0, 2024, "FY", None, "2024-12-31",
         "2025-02-01", "2025-02-01T23:59:59", "10-K", "a", "sec"),
    ])

    assert store.get_pit_value("TEST", "Revenue", 2024, "FY", "2025-02-01")["val"] == 100.0
