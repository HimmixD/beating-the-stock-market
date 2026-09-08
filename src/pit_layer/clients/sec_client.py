import os
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

class SecClient:
    def __init__(self):
        self.user_agent = os.getenv("SEC_USER_AGENT")
        if not self.user_agent:
            raise ValueError("SEC_USER_AGENT fehlt in der .env Datei.")
        self.headers = {"User-Agent": self.user_agent}

    def fetch(self, url: str) -> dict:
        """Führt einen Request mit Jitter, Rate-Limiting und Retry-Logik aus."""
        # Basis-Delay + Jitter
        time.sleep(0.12 + random.uniform(0.02, 0.08)) 
        
        for attempt in range(3):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429: # Rate Limit Hit
                    time.sleep(2 ** attempt + random.uniform(0.1, 0.5))
                else:
                    response.raise_for_status()
            except requests.RequestException as e:
                print(f"Netzwerkfehler bei SEC API: {e}. Versuch {attempt + 1}/3")
                time.sleep(1 + attempt)
                
        raise ConnectionError(f"SEC URL konnte nicht geladen werden: {url}")

    def fetch_tickers(self) -> dict:
        # HIER WURDE DIE URL KORRIGIERT:
        return self.fetch("https://www.sec.gov/files/company_tickers.json")

    def fetch_company_facts(self, cik: str) -> dict:
        return self.fetch(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")