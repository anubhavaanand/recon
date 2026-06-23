import asyncio
import base64
import time
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
        from clients.scrapers import search_wipo_patents
        return await search_wipo_patents(query)

class EPOClient(BaseAsyncClient):
    """EPO client with API-first, scraper-fallback pipeline.

    Attempts the official EPO OPS REST API first. Falls back to a
    DuckDuckGo + BeautifulSoup scraper if credentials are missing,
    invalid, or the API returns any error.
    """

    def __init__(self):
        super().__init__(base_url="https://ops.epo.org/3.2", timeout=30.0)
        self.config = load_config()
        self.access_token: str | None = None
        self.token_expiry: float = 0
        # EPO Rate limit: 3/sec (24% headroom)
        self.rate_limit_delay = 1.0 / (3.0 * 0.76)

    async def _get_access_token(self) -> str | None:
        """Obtain a Bearer token via OAuth 2.0 Client Credentials grant.

        Returns the token string, or None if keys are missing/invalid.
        """
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token

        key = self.config.epo_consumer_key
        secret = self.config.epo_consumer_secret
        if not key or not secret:
            return None

        auth_str = f"{key}:{secret}"
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            client = await self.get_client()
            response = await client.post(
                "https://ops.epo.org/3.2/auth/accesstoken",
                data={"grant_type": "client_credentials"},
                headers=headers,
            )
            if response.status_code != 200:
                return None
            data = response.json()
            self.access_token = data.get("access_token")
            expires_in = int(data.get("expires_in", 1200))
            self.token_expiry = time.time() + expires_in - 60
            return self.access_token
        except Exception:
            self.access_token = None
            return None

    async def validate_credentials(self) -> tuple[bool, str]:
        """Validate EPO credentials. Returns (ok, message)."""
        key = self.config.epo_consumer_key
        secret = self.config.epo_consumer_secret
        if not key or not secret:
            return False, "Missing/invalid keys. Falling back to scraper."

        self.access_token = None
        token = await self._get_access_token()
        if token:
            return True, "EPO API Key is VALID."
        return False, "Missing/invalid keys. Falling back to scraper."

    async def search(self, query: str) -> List[PatentRecord]:
        """API-first search; falls back to scraper on any failure."""
        token = await self._get_access_token()
        if token:
            try:
                records = await self._search_ops_api(query, token)
                if records:
                    return records
            except Exception:
                pass

        from clients.scrapers import search_epo_patents
        return await search_epo_patents(query)

    async def _search_ops_api(self, query: str, token: str) -> List[PatentRecord]:
        """Search the official EPO OPS REST API and map to PatentRecord."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        cql = f'txt="{query}"'
        
        await asyncio.sleep(self.rate_limit_delay)
        
        response = await self.get_with_backoff(
            "/rest-services/published-data/search/biblio",
            params={"q": cql},
            headers=headers,
        )
        if response.status_code != 200:
            response.raise_for_status()

        data = response.json()
        exchange_docs = (
            data.get("ops:world-patent-data", {})
            .get("ops:biblio-search", {})
            .get("ops:search-result", {})
            .get("exchange-documents", [])
        )
        if isinstance(exchange_docs, dict):
            exchange_docs = [exchange_docs]

        records: list[PatentRecord] = []
        for doc in exchange_docs:
            ed = doc.get("exchange-document", {})
            biblio = ed.get("bibliographic-data", {})
            country = ed.get("@country", "UN")
            doc_num = ed.get("@doc-number", "UNKNOWN")
            pid = f"{country}{doc_num}"

            titles = biblio.get("invention-title", [])
            if isinstance(titles, dict):
                titles = [titles]
            title = next(
                (t.get("$", "[?]") for t in titles if t.get("@lang") == "en"),
                titles[0].get("$", "[?]") if titles else "[?]",
            )

            abstracts = biblio.get("abstract", [])
            if isinstance(abstracts, dict):
                abstracts = [abstracts]
            abstract = "[?]"
            for a in abstracts:
                if isinstance(a, dict) and a.get("@lang") == "en":
                    p = a.get("p", {})
                    if isinstance(p, dict):
                        abstract = p.get("$", "[?]")
                    break

            parties = biblio.get("parties", {}).get("applicants", {}).get("applicant", [])
            if isinstance(parties, dict):
                parties = [parties]
            assignee = parties[0].get("applicant-name", {}).get("name", {}).get("$", "[?]") if parties else "[?]"

            date_refs = biblio.get("publication-reference", {}).get("document-id", [])
            if isinstance(date_refs, dict):
                date_refs = [date_refs]
            filed = date_refs[0].get("date", {}).get("$", "[?]") if date_refs else "[?]"
            if filed != "[?]" and len(filed) == 8:
                filed = f"{filed[:4]}-{filed[4:6]}-{filed[6:]}"

            records.append(PatentRecord(
                id=pid,
                title=title,
                assignee=assignee,
                dates={"filed": filed},
                abstract=abstract,
                claims=[],
                image_urls=[],
                status="active",
                family_id=ed.get("@family-id", "UNKNOWN"),
            ))

        return records

    async def _search_epo_duckduckgo(self, query: str) -> List[PatentRecord]:
        """Fallback: mock data when API is unavailable."""
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
                family_id="F-EPO-1",
            ),
        ]

class LensClient(BaseAsyncClient):
    """Lens.org client returning mock data (no free API available)."""

    def __init__(self):
        super().__init__(base_url="https://www.lens.org", timeout=30.0)
        self.config = load_config()

    async def validate_credentials(self) -> tuple[bool, str]:
        return True, "Lens client (mock data)."

    async def search(self, query: str) -> List[PatentRecord]:
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
        from clients.scrapers import search_google_patents
        return await search_google_patents(query)
