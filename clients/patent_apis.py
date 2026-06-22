import asyncio
from typing import List
from clients.base import BaseAsyncClient
from core.models import PatentRecord
from core.config import load_config

class USPTOClient(BaseAsyncClient):
    def __init__(self):
        super().__init__(base_url="https://api.uspto.gov/api/v1", timeout=30.0)
        self.config = load_config()
        # Rate limit: 76/min (24% headroom) -> ~0.78s between requests
        self.rate_limit_delay = 60.0 / 76.0

    async def validate_credentials(self) -> tuple[bool, str]:
        if not self.config.uspto_api_key:
            return False, "ERR: USPTO API key missing."
        
        headers = {"X-API-KEY": self.config.uspto_api_key}
        params = {"query": "battery"} # minimal search to validate
        try:
            client = await self.get_client()
            response = await client.get(self.base_url + "/patent/applications/search", params=params, headers=headers)
            if response.status_code == 200:
                return True, "USPTO Key is VALID."
            elif response.status_code in [401, 403]:
                return False, f"ERR: USPTO authentication failed (Status {response.status_code})."
            else:
                return False, f"ERR: USPTO returned status {response.status_code}."
        except Exception as e:
            return False, f"ERR: USPTO validation error: {str(e)}"

    async def search(self, query: str) -> List[PatentRecord]:
        if not self.config.uspto_api_key:
            # According to specs: "ERR: Source [Lens] rate limit exceeded. Provide API key via LENS_API_KEY."
            # We follow similar pattern for USPTO
            print("ERR: Source [USPTO] API key missing. Provide via 'recon config set --uspto-key'.")
            return []

        headers = {"X-API-KEY": self.config.uspto_api_key}
        params = {"query": query}
        
        try:
            # Rate limiting delay
            await asyncio.sleep(self.rate_limit_delay)
            
            response = await self.get_with_backoff("/patent/applications/search", params=params, headers=headers)
            if response.status_code != 200:
                print(f"ERR: Source [USPTO] failed with status {response.status_code}")
                return []
            
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            
            records = []
            for doc in docs:
                records.append(PatentRecord(
                    id=doc.get("patentNumber") or doc.get("applicationNumberText") or "UNKNOWN",
                    title=doc.get("inventionTitle", "[?]"),
                    assignee=doc.get("applicantName", "[?]"),
                    dates={"filed": doc.get("filingDate", "[?]")},
                    abstract=" ".join(doc.get("abstractText", ["[?]"])),
                    claims=[],  # Detailed data on demand
                    image_urls=[],
                    status=doc.get("applicationStatusCategory", "UNKNOWN"),
                    family_id="UNKNOWN"
                ))
            return records
        except Exception as e:
            print(f"ERR: Source [USPTO] failed: {e}")
            return []

class WIPOClient(BaseAsyncClient):
    def __init__(self):
        super().__init__(base_url="https://patentscope.wipo.int", timeout=30.0)

    async def search(self, query: str) -> List[PatentRecord]:
        try:
            from clients.scrapers import search_wipo_patents
            records = await search_wipo_patents(query)
            if records:
                return records
        except Exception as e:
            print(f"ERR: Source [WIPO] scraper failed: {e}")

        print(f"INFO: Source [WIPO] using mock data for '{query}'.")
        return [
            PatentRecord(
                id=f"WO-{query[:4].upper()}",
                title=f"WIPO Result for {query}",
                assignee="WIPO Assignee",
                dates={"filed": "2023-01-01"},
                abstract=f"A WIPO patent related to {query}.",
                claims=[],
                image_urls=[],
                status="active",
                family_id="F123"
            ),
        ]

class EPOClient(BaseAsyncClient):
    """EPO client using DuckDuckGo discovery + snippet scraping.

    EPO Register and Espacenet are behind Cloudflare and require OAuth for
    the official OPS API. We bypass both with a free DDGS+BS4 scraper,
    falling back to mock data when scraping fails.
    """

    def __init__(self):
        super().__init__(base_url="https://register.epo.org", timeout=30.0)
        self.config = load_config()

    async def validate_credentials(self) -> tuple[bool, str]:
        # EPO scraper requires no credentials
        return True, "EPO scraper (no credentials needed)."

    async def search(self, query: str) -> List[PatentRecord]:
        try:
            from clients.scrapers import search_epo_patents
            records = await search_epo_patents(query)
            if records:
                return records
        except Exception as e:
            print(f"ERR: Source [EPO] scraper failed: {e}")

        print(f"INFO: Source [EPO] using mock data for '{query}'.")
        return [
            PatentRecord(
                id=f"EP-MOCK-{query[:4].upper()}",
                title=f"EPO Result for {query}",
                assignee="EPO Assignee GmbH",
                dates={"filed": "2023-06-15"},
                abstract=f"A European patent related to {query}.",
                claims=[],
                image_urls=[],
                status="active",
                family_id="F-EPO-1"
            ),
        ]

class LensClient(BaseAsyncClient):
    """Lens.org client using DuckDuckGo discovery + snippet scraping.

    Lens.org's API requires a paid key and their patent pages are JS-rendered.
    We bypass both with a free DDGS+BS4 scraper, falling back to mock data
    when scraping fails.
    """

    def __init__(self):
        super().__init__(base_url="https://www.lens.org", timeout=30.0)
        self.config = load_config()

    async def validate_credentials(self) -> tuple[bool, str]:
        # Lens scraper requires no credentials
        return True, "Lens scraper (no credentials needed)."

    async def search(self, query: str) -> List[PatentRecord]:
        try:
            from clients.scrapers import search_lens_patents
            records = await search_lens_patents(query)
            if records:
                return records
        except Exception as e:
            print(f"ERR: Source [Lens] scraper failed: {e}")

        print(f"INFO: Source [Lens] using mock data for '{query}'.")
        return [
            PatentRecord(
                id=f"LN-MOCK-{query[:4].upper()}",
                title=f"Lens.org Result for {query}",
                assignee="Lens Assignee Ltd.",
                dates={"filed": "2023-09-01"},
                abstract=f"A Lens.org patent related to {query}.",
                claims=[],
                image_urls=[],
                status="active",
                family_id="F-LENS-1"
            ),
        ]

    async def fetch_citations(self, patent_id: str) -> dict:
        """Lens citation fetching is not available via scraper.

        Returns empty results since Lens.org API requires a paid key.
        Citation graph will show None found.
        """
        return {"forward": [], "backward": []}

class PatsnapClient(BaseAsyncClient):
    """PatSnap (Eureka Open Platform) client using P002 Analytics Query Search (v2).

    Docs: https://open.patsnap.com/devportal/api-reference/search/patent/query-search-patent
    Endpoint: POST https://connect.patsnap.com/search/patent/query-search-patent/v2
    Auth: Bearer token via Authorization header.
    """

    def __init__(self):
        super().__init__(base_url="https://connect.patsnap.com", timeout=30.0)
        self.config = load_config()
        self._api_key: str | None = None

    def _resolve_key(self) -> str | None:
        if self._api_key:
            return self._api_key
        key = self.config.patsnap_api_key
        if key:
            self._api_key = key
        return self._api_key

    def _headers(self) -> dict[str, str]:
        key = self._resolve_key()
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    async def validate_credentials(self) -> tuple[bool, str]:
        key = self._resolve_key()
        if not key:
            return False, "ERR: PatSnap API key missing. Set via 'recon config set --patsnap-key' or PATSNAP_API_KEY in .env."

        import json
        payload = {
            "query_text": "TACD: battery",
            "limit": 1,
            "offset": 0,
            "stemming": 0,
        }
        try:
            client = await self.get_client()
            response = await client.post(
                self.base_url + "/search/patent/query-search-patent/v2",
                headers=self._headers(),
                json=payload,
            )
            if response.status_code == 200:
                return True, "PatSnap Key is VALID."
            elif response.status_code in [401, 403]:
                return False, f"ERR: PatSnap authentication failed (Status {response.status_code})."
            else:
                body = response.json()
                code = body.get("error_code", response.status_code)
                msg = body.get("error_msg", "unknown error")
                return False, f"ERR: PatSnap returned error {code}: {msg}"
        except Exception as e:
            return False, f"ERR: PatSnap validation error: {e}"

    async def search(self, query: str) -> List[PatentRecord]:
        key = self._resolve_key()
        if not key:
            print("ERR: Source [PatSnap] API key missing. Provide via 'recon config set --patsnap-key' or PATSNAP_API_KEY in .env.")
            return []

        import json
        payload = {
            "query_text": f"TACD: {query}",
            "collapse_type": "DOCDB",
            "collapse_by": "PBD",
            "collapse_order": "LATEST",
            "sort": [{"field": "SCORE", "order": "DESC"}],
            "limit": 10,
            "offset": 0,
            "stemming": 0,
        }
        try:
            client = await self.get_client()
            response = await client.post(
                self.base_url + "/search/patent/query-search-patent/v2",
                headers=self._headers(),
                json=payload,
            )
            if response.status_code != 200:
                body = response.json()
                code = body.get("error_code", response.status_code)
                msg = body.get("error_msg", f"HTTP {response.status_code}")
                print(f"ERR: Source [PatSnap] failed — error {code}: {msg}")
                return []

            body = response.json()
            if not body.get("status"):
                code = body.get("error_code", "?")
                msg = body.get("error_msg", "unknown error")
                print(f"ERR: Source [PatSnap] returned error {code}: {msg}")
                return []

            results = body.get("data", {}).get("results", [])
            records: list[PatentRecord] = []
            for doc in results:
                pn = doc.get("pn") or "UNKNOWN"
                title = doc.get("title") or "[?]"
                assignee = doc.get("current_assignee") or doc.get("original_assignee") or "[?]"

                dates: dict[str, str] = {}
                pbdt = doc.get("pbdt")
                if pbdt:
                    d = str(pbdt)
                    dates["published"] = f"{d[:4]}-{d[4:6]}-{d[6:]}"
                apdt = doc.get("apdt")
                if apdt:
                    d = str(apdt)
                    dates["filed"] = f"{d[:4]}-{d[4:6]}-{d[6:]}"
                if not dates:
                    dates = {"filed": "[?]"}

                records.append(PatentRecord(
                    id=pn,
                    title=title,
                    assignee=assignee,
                    dates=dates,
                    abstract="[?]",
                    claims=[],
                    image_urls=[],
                    status="active",
                    family_id="UNKNOWN",
                ))
            return records
        except Exception as e:
            print(f"ERR: Source [PatSnap] failed: {e}")
            return []


class GooglePatentsClient(BaseAsyncClient):
    async def search(self, query: str) -> List[PatentRecord]:
        try:
            from clients.scrapers import search_google_patents
            records = await search_google_patents(query)
            if records:
                return records
        except Exception as e:
            print(f"ERR: Source [GooglePatents] scraper failed: {e}")

        print(f"INFO: Source [GooglePatents] using mock data for '{query}'.")
        return [
            PatentRecord(
                id=f"US-MOCK-{query[:3].upper()}-1",
                title=f"Mock System for {query.title()}",
                assignee="Mock Assignee Inc.",
                dates={"filed": "2023-10-01"},
                abstract=f"A novel approach to {query} utilizing mock algorithms.",
                claims=["1. A system comprising a mock processor.", "2. The system of claim 1, further comprising mock memory."],
                image_urls=[],
                status="active",
                family_id="F-MOCK-1"
            ),
            PatentRecord(
                id=f"EP-MOCK-{query[:3].upper()}-2",
                title=f"Advanced {query.title()} Methods",
                assignee="Global Mock Corp.",
                dates={"filed": "2022-05-15"},
                abstract=f"An advanced method for implementing {query} in distributed systems.",
                claims=[
                    f"1. A method for {query}.",
                    f"2. The method of claim 1, further comprising a verification step.",
                ],
                image_urls=[],
                status="pending",
                family_id="F-MOCK-2"
            ),
        ]
