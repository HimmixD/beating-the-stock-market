import csv
import os
import pytest
from pit_layer.router import PitRouter

def load_golden_cases():
    csv_path = os.path.join(os.path.dirname(__file__), "golden_cases.csv")
    if not os.path.exists(csv_path):
        return []
    
    cases = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cases.append(row)
    return cases

@pytest.fixture
def router():
    return PitRouter()

@pytest.mark.parametrize("case", load_golden_cases(), ids=lambda c: c["case_id"])
def test_golden_case_from_csv(router, case):
    symbol = case["symbol"]
    field = case["field"]
    fiscal_year = int(case["fiscal_year"])
    fiscal_period = case["fiscal_period"]
    
    # Normalisierung des Timestamps für SQLite-Vergleich
    raw_as_of = case["as_of_iso"]
    as_of_iso = raw_as_of.replace("Z", "").split("+")[0]
    
    expect_success = case["expect_success"].lower() == "true"
    
    result = router.get_value(symbol, field, fiscal_year, period=fiscal_period, as_of_date=as_of_iso)
    
    if not expect_success:
        assert result is None, f"[{case['case_id']}] Look-Ahead-Fehler! Erwartete KEINEN Wert, bekam aber: {result}"
    else:
        assert result is not None, f"[{case['case_id']}] Erwartete einen Wert, bekam aber None."
        
        expected_val = float(case["expected_value"])
        tolerance = float(case["expected_value_tol"])
        assert abs(result["val"] - expected_val) <= tolerance, f"[{case['case_id']}] Wertweichung! Erwartet: {expected_val}, Erhalten: {result['val']}"