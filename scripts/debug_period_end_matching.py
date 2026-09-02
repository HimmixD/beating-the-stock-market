
from datetime import date, datetime

from quant.data.sec_client import SECClient
from quant.validation.concept_map import SEC_CONCEPTS

sec_client = SECClient()

from datetime import date

facts = sec_client.get_facts(
    cik="0000320193",
    concepts=[
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsToAcquireBusinessesNetOfCashAcquired",
        "PaymentsForProceedsFromOtherInvestingActivities",
        "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciation",
    ],
)

for fact in facts:
    if fact.period_end == date(2009, 9, 26):
        print(fact)
        