import requests
import xml.etree.ElementTree as ET
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

CIK = "0000320193"
ACCESSION = "0001193125-09-214859"

ACCESSION_NO_DASH = ACCESSION.replace("-", "")

HEADERS = {
    "User-Agent": "QuantResearch/1.0 himmelias@gmail.com"
}


# ============================================================
# DOWNLOAD ORIGINAL XBRL
# ============================================================

url = (
    f"https://www.sec.gov/Archives/edgar/data/"
    f"{int(CIK)}/{ACCESSION_NO_DASH}/"
    f"aapl-20090926.xml"
)

print("=" * 80)
print("DOWNLOADING ORIGINAL SEC XBRL")
print("=" * 80)

print(url)

response = requests.get(
    url,
    headers=HEADERS
)

print("\nStatus:", response.status_code)
print("Size:", len(response.content), "bytes")

response.raise_for_status()


# ============================================================
# PARSE XML
# ============================================================

root = ET.fromstring(
    response.content
)


# ============================================================
# EXTRACT ALL FACTS CONTAINING ASSET / LIABILITY / EQUITY
# ============================================================

print("\n")
print("=" * 80)
print("RELEVANT XBRL FACTS")
print("=" * 80)


rows = []


for element in root.iter():

    tag = element.tag.split("}")[-1]

    if any(
        keyword in tag.lower()
        for keyword in [
            "assets",
            "liabilities",
            "equity"
        ]
    ):

        rows.append(
            {
                "tag": tag,
                "value": element.text,
                "contextRef": element.attrib.get(
                    "contextRef"
                ),
                "unitRef": element.attrib.get(
                    "unitRef"
                ),
            }
        )


df = pd.DataFrame(rows)


print(
    df.to_string(index=False)
)

# ============================================================
# FIND EXACT ASSETS / LIABILITIES / EQUITY FACTS
# ============================================================

print("\n")
print("=" * 80)
print("EXACT BALANCE SHEET FACTS")
print("=" * 80)


targets = [
    "Assets",
    "Liabilities",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
]


for target in targets:

    matches = df[
        df["tag"] == target
    ]

    if not matches.empty:

        print("\n" + "-" * 80)
        print(target)

        print(
            matches.to_string(index=False)
        )

# ============================================================
# PRINT CONTEXTS FOR ASSETS
# ============================================================

print("\n")
print("=" * 80)
print("ASSETS CONTEXTS")
print("=" * 80)


# Find all Assets elements
assets_elements = []

for element in root.iter():

    tag = element.tag.split("}")[-1]

    if tag == "Assets":

        assets_elements.append(element)


for element in assets_elements:

    context_ref = element.attrib.get(
        "contextRef"
    )

    print("\n")
    print(
        "Value:",
        element.text
    )

    print(
        "Context:",
        context_ref
    )

    # Find matching context
    for context in root.iter():

        context_tag = context.tag.split("}")[-1]

        if (
            context_tag == "context"
            and context.attrib.get("id")
            == context_ref
        ):

            print(
                ET.tostring(
                    context,
                    encoding="unicode"
                )
            )