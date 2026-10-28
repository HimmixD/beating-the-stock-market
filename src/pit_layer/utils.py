from typing import Optional

SEC_CONCEPT_MAP = {
    "revenue": [
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenuesNetOfInterestExpense",
        # Additional common variations
        "Revenue",
        "TotalRevenue",
        "RevenueBeforeTax",
    ],
    "net_income": [
        "NetIncomeLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
        "ProfitLoss",
        # Additional common variations
        "NetIncome",
        "IncomeLoss",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "OperatingIncome",
    ],
    "gross_profit": [
        "GrossProfit",
        "GrossProfitLoss",
    ],
    "assets": [
        "Assets",
        "TotalAssets",
    ],
    "total_assets": [
        "Assets",
        "TotalAssets",
        # <-- HinzugefÃ¼gt, damit die CSV-Feldnamen matchen
    ],
    "liabilities": [
        "Liabilities",
        "TotalLiabilities",
    ],
    "equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "TotalEquity",
        "ShareholdersEquity",
    ],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "OperatingCashFlow",
    ],
    "cash": [
        "CashAndCashEquivalents",
        "CashCashEquivalent",
        # <-- HinzugefÃ¼gt fÃ¼r Statement-Typen
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "CapitalExpenditure",
        "CapEx",
    ],
    "research_development": [
        "PaymentsForResearchAndDevelopment",
        "ResearchDevelopmentCosts",
    ],
    "depreciation": [
        "Depreciation",
        "DepreciationAndAmortization",
    ],
    "interest_expense": [
        "InterestExpense",
        "InterestCost",
    ],
    "tax_expense": [
        "TaxExpense",
        "ProvisionForIncomeTax",
    ],
    "earnings_per_share": [
        "EarningsPerShareBasic",
        "EarningsPerShareDiluted",
    ],
    "dividends": [
        "CashDividendsPerShare",
        "DividendsPerShare",
    ],
}

def _fuzzy_concept_match(concept: str, possible_concepts: list) -> Optional[str]:
    """
    Fuzzy match a concept name against possible concept names.
    Uses simple substring matching as a fallback when exact match fails.
    """
    concept_lower = concept.lower()

    # First try exact match (case-insensitive)
    for possible in possible_concepts:
        if possible.lower() == concept_lower:
            return possible

    # Try substring match: if concept is substring of possible or vice versa
    for possible in possible_concepts:
        if concept_lower in possible.lower() or possible.lower() in concept_lower:
            return possible

    # Try startswith match
    for possible in possible_concepts:
        if possible.lower().startswith(concept_lower) or concept_lower.startswith(possible.lower()):
            return possible

    return None


def get_possible_concepts(concept: str) -> list:
    """Get possible concept names from SEC_CONCEPT_MAP, with fuzzy fallback."""
    possible = SEC_CONCEPT_MAP.get(concept.lower())
    if possible:
        return possible

    # If not in map, return list with the original concept name
    # This allows the providers to try fetching with the exact name
    return [concept]
