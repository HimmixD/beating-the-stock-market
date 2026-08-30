import os
from dotenv import load_dotenv
import requests
from .models import FilingFact
from datetime import date, datetime
from typing import Any

load_dotenv()

class SECClient:

    BASE_URL = "https://data.sec.gov"

    def __init__(self):

        user_agent = os.getenv("SEC_USER_AGENT")

        if not user_agent:
            raise RuntimeError(
                "SEC_USER_AGENT environment variable is not set."
            )

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        })

    def get_company_facts(self, cik: str) -> dict[str, Any]:

        cik = str(cik).zfill(10)

        url = (
            f"{self.BASE_URL}/api/xbrl/companyfacts/"
            f"CIK{cik}.json"
        )

        response = self.session.get(url, timeout=30)

        response.raise_for_status()

        return response.json()

    def get_facts(
        self,
        cik: str,
        concepts: list[str],
    ) -> list[FilingFact]:

        company_facts = self.get_company_facts(cik)

        facts = []

        us_gaap = company_facts.get("facts", {}).get("us-gaap", {})

        for concept in concepts:

            if concept not in us_gaap:
                continue

            concept_data = us_gaap[concept]

            units = concept_data.get("units", {})

            for unit_name, unit_facts in units.items():

                for fact in unit_facts:

                    if "end" not in fact:
                        continue

                    period_start = None

                    if "start" in fact:
                        period_start = date.fromisoformat(
                            fact["start"]
                        )

                    period_end = date.fromisoformat(
                        fact["end"]
                    )

                    filing_date = None

                    if fact.get("filed"):
                        filing_date = date.fromisoformat(
                            fact["filed"]
                        )

                    accepted_date = None

                    if fact.get("accn"):
                        # Accepted timestamp isn't always exposed
                        # in Company Facts.
                        accepted_date = None

                    facts.append(
                        FilingFact(
                            concept=concept,
                            value=float(fact["val"]),
                            unit=unit_name,
                            period_start=period_start,
                            period_end=period_end,
                            fiscal_year=fact.get("fy"),
                            fiscal_period=fact.get("fp"),
                            filing_date=filing_date,
                            accepted_date=accepted_date,
                            form=fact.get("form"),
                            accession_number=fact.get("accn"),
                            cik=str(cik).zfill(10),
                        )
                    )

        return facts