import os

from datetime import date, datetime
from typing import Any

import requests
from dotenv import load_dotenv

from .models import FilingFact
from .request_utils import (
    create_resilient_session,
    resilient_get,
)

load_dotenv()


class SECClient:

    BASE_URL = "https://data.sec.gov"
    SEC_BASE_URL = "https://www.sec.gov"

    def __init__(self):

        user_agent = os.getenv("SEC_USER_AGENT")

        if not user_agent:
            raise RuntimeError(
                "SEC_USER_AGENT environment variable is not set."
            )

        self.session = create_resilient_session(
            user_agent=user_agent,
        )

        self.session.headers.update({
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        })

        self._accepted_dates: dict[str, dict[str, datetime | None]] = {}
        self._company_facts: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _to_utc_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    # ... keep get_company_facts / get_submission_history / _columnar_to_records unchanged ...

    @staticmethod
    def _parse_accepted_datetime(
        value: Any,
    ) -> datetime | None:

        if not value:
            return None

        if isinstance(value, datetime):
            return SECClient._to_utc_aware(value)

        value = str(value)

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
            return SECClient._to_utc_aware(parsed)
        except ValueError:
            pass

        try:
            parsed = datetime.strptime(
                value,
                "%Y%m%d%H%M%S",
            )
            return SECClient._to_utc_aware(parsed)
        except ValueError:
            return None

    def get_company_facts(
        self,
        cik: str,
    ) -> dict[str, Any]:

        cik = str(cik).zfill(10)

        # ---------------------------------------------------------------
        # In-memory cache
        # ---------------------------------------------------------------

        if cik in self._company_facts:
            return self._company_facts[cik]

        url = (
            f"{self.BASE_URL}/api/xbrl/companyfacts/"
            f"CIK{cik}.json"
        )

        response = resilient_get(
            self.session,
            url,
        )

        response.raise_for_status()

        data = response.json()

        self._company_facts[cik] = data

        return data

    def get_submission_history(
        self,
        cik: str,
    ) -> list[dict[str, Any]]:

        """
        Return SEC filing metadata for all available submissions.

        The current submissions JSON contains recent filings directly.
        Older filings are referenced through additional JSON files in
        the 'files' section.
        """

        cik = str(cik).zfill(10)

        url = (
            f"{self.BASE_URL}/submissions/"
            f"CIK{cik}.json"
        )

        response = resilient_get(
            self.session,
            url,
        )

        response.raise_for_status()

        data = response.json()

        filings = []

        recent = data.get("filings", {}).get("recent", {})

        filings.extend(
            self._columnar_to_records(recent)
        )

        for file_info in data.get("filings", {}).get(
            "files",
            [],
        ):

            file_name = file_info.get("name")

            if not file_name:
                continue

            file_url = (
                f"{self.BASE_URL}/submissions/"
                f"{file_name}"
            )

            file_response = resilient_get(
                self.session,
                file_url,
            )

            file_response.raise_for_status()

            historical_data = file_response.json()

            filings.extend(
                self._columnar_to_records(
                    historical_data
                )
            )

        return filings

    @staticmethod
    def _columnar_to_records(
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        """
        Convert SEC's column-oriented submissions data into
        one dictionary per filing.
        """

        if not data:
            return []

        keys = list(data.keys())

        if not keys:
            return []

        row_count = len(data[keys[0]])

        records = []

        for index in range(row_count):

            record = {
                key: data[key][index]
                for key in keys
                if index < len(data[key])
            }

            records.append(record)

        return records

    def get_accepted_dates(
        self,
        cik: str,
    ) -> dict[str, datetime | None]:

        """
        Return a mapping:

            accession_number -> accepted datetime

        for all SEC submissions available for the company.
        """

        cik = str(cik).zfill(10)

        if cik in self._accepted_dates:
            return self._accepted_dates[cik]

        submissions = self.get_submission_history(cik)

        accepted_dates = {}

        for submission in submissions:

            accession = submission.get(
                "accessionNumber"
            )

            if not accession:
                continue

            accepted_datetime = self._parse_accepted_datetime(
                submission.get("acceptanceDateTime")
            )

            accepted_dates[accession] = accepted_datetime

        self._accepted_dates[cik] = accepted_dates

        return accepted_dates

    @staticmethod
    def _parse_accepted_datetime(
        value: Any,
    ) -> datetime | None:

        if not value:
            return None

        if isinstance(value, datetime):
            return value

        value = str(value)

        # SEC submissions normally use ISO-style timestamps.
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            pass

        # Fallback for compact SEC timestamp format.
        try:
            return datetime.strptime(
                value,
                "%Y%m%d%H%M%S",
            )
        except ValueError:
            return None

    def get_facts(
        self,
        cik: str,
        concepts: list[str],
    ) -> list[FilingFact]:

        cik = str(cik).zfill(10)

        company_facts = self.get_company_facts(cik)

        # -----------------------------------------------------------
        # SEC filing metadata
        # -----------------------------------------------------------

        accepted_dates = self.get_accepted_dates(cik)

        facts = []

        us_gaap = (
            company_facts
            .get("facts", {})
            .get("us-gaap", {})
        )

        for concept in concepts:

            if concept not in us_gaap:
                continue

            concept_data = us_gaap[concept]

            units = concept_data.get(
                "units",
                {},
            )

            for unit_name, unit_facts in units.items():

                for fact in unit_facts:

                    if "end" not in fact:
                        continue

                    # ------------------------------------------------
                    # Period
                    # ------------------------------------------------

                    period_start = None

                    if fact.get("start"):
                        period_start = date.fromisoformat(
                            fact["start"]
                        )

                    period_end = date.fromisoformat(
                        fact["end"]
                    )

                    # ------------------------------------------------
                    # Filing date
                    # ------------------------------------------------

                    filing_date = None

                    if fact.get("filed"):
                        filing_date = date.fromisoformat(
                            fact["filed"]
                        )

                    # ------------------------------------------------
                    # Acceptance timestamp
                    # ------------------------------------------------

                    accession_number = fact.get("accn")

                    accepted_date = None

                    if accession_number:
                        accepted_date = accepted_dates.get(
                            accession_number
                        )

                    # ------------------------------------------------
                    # FilingFact
                    # ------------------------------------------------

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
                            accession_number=accession_number,
                            cik=cik,
                        )
                    )

        return facts

    def get_filings(
        self,
        cik: str,
    ) -> list[dict[str, Any]]:

        """
        Return SEC filing metadata enriched with parsed acceptance
        timestamps.
        """

        submissions = self.get_submission_history(cik)

        filings = []

        for submission in submissions:

            accession = submission.get(
                "accessionNumber"
            )

            if not accession:
                continue

            filing = dict(submission)

            filing["accepted_date"] = (
                self._parse_accepted_datetime(
                    submission.get("acceptanceDateTime")
                )
            )

            filings.append(filing)

        return filings