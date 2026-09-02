OPENBB_FIELDS = {
    # Income statement
    "revenue": [
        "total_revenue",
        "operating_revenue",
        "revenue",
    ],

    "gross_profit": [
        "gross_profit",
        "total_gross_profit",
    ],

    "operating_income": [
        "total_operating_income",
    ],

    "net_income": [
        "net_income",
    ],

    # Balance sheet
    "total_assets": [
        "total_assets",
    ],

    "total_liabilities": [
        "total_liabilities",
    ],

    "stockholders_equity": [
        "total_common_equity",
    ],

    "cash_and_cash_equivalents": [
        "cash_and_equivalents",
    ],

    # Cash flow statement
    "operating_cash_flow": [
        "net_cash_from_operating_activities",
        "net_cash_from_continuing_operating_activities",
    ],

    "capital_expenditures": [
        "capital_expenditure",
        "purchase_of_plant_property_and_equipment",
    ],
}


SEC_CONCEPTS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],

    "gross_profit": [
        "GrossProfit",
    ],

    "operating_income": [
        "OperatingIncomeLoss",
    ],

    "net_income": [
        "ProfitLoss",
        "NetIncomeLoss",
    ],

    "total_assets": [
        "Assets",
    ],

    "total_liabilities": [
        "Liabilities",
    ],

    "stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],

    "cash_and_cash_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
    ],

    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
    ],

    "capital_expenditures": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],

    "income_tax_expense": [
        "IncomeTaxExpenseBenefit",
    ],

    "depreciation": [
        "DepreciationDepletionAndAmortization",
        "DepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
    ],

    "depreciation_and_amortization": [
        "DepreciationDepletionAndAmortization",
        "DepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
    ],

    "basic_eps": [
        "EarningsPerShareBasic",
    ],

    "diluted_eps": [
        "EarningsPerShareDiluted",
    ],

    "weighted_average_basic_shares": [
        "WeightedAverageNumberOfSharesOutstandingBasic",
    ],

    "weighted_average_diluted_shares": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ],

    "dividends_per_share": [
        "CommonStockDividendsPerShareDeclared",
    ],
}