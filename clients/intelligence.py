import httpx
import asyncio
from typing import List
from core.models import CrossReference
import urllib.parse

class IntelligenceClient:
    """Client for gathering cross-reference intelligence."""
    
    def __init__(self):
        self.timeout = 15.0

    async def fetch_nih_reporter(self, entity_name: str) -> List[CrossReference]:
        url = "https://api.reporter.nih.gov/v2/projects/search"
        payload = {
            "criteria": {
                "pi_names": [{"first_name": entity_name, "last_name": ""}] # Approximation
            },
            "limit": 5
        }
        # A real implementation would try matching assignee/inventors more intelligently
        # We will do a generic query on org_names or pi_names depending on entity
        payload = {
            "criteria": {
                "org_names": [entity_name]
            },
            "limit": 5
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    refs = []
                    for r in results:
                        proj_num = r.get("project_num", "UNKNOWN")
                        title = r.get("project_title", "")
                        refs.append(CrossReference(
                            source="NIH", 
                            url=f"https://reporter.nih.gov/search/search/project-details/{proj_num}",
                            metadata={"confidence": 85.0, "title": title}
                        ))
                    return refs
                return []
        except Exception as e:
            print(f"ERR: NIH RePORTER fetch failed: {e}")
            return []

    async def fetch_openalex(self, entity_name: str) -> List[CrossReference]:
        # Search institutions or works
        query = urllib.parse.quote(entity_name)
        url = f"https://api.openalex.org/institutions?search={query}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    if not results:
                        return []
                    inst_id = results[0].get("id")
                    
                    # fetch works from this institution
                    works_url = f"https://api.openalex.org/works?filter=institutions.id:{inst_id.split('/')[-1]}&per-page=5"
                    works_resp = await client.get(works_url)
                    if works_resp.status_code == 200:
                        works = works_resp.json().get("results", [])
                        refs = []
                        for w in works:
                            refs.append(CrossReference(
                                source="OpenAlex",
                                url=w.get("id", ""),
                                metadata={"confidence": 90.0, "title": w.get("title", "")}
                            ))
                        return refs
                return []
        except Exception as e:
            print(f"ERR: OpenAlex fetch failed: {e}")
            return []

    async def fetch_signals(self, entity_name: str) -> List[CrossReference]:
        if not entity_name or entity_name == "[?]":
            return []
            
        tasks = [
            self.fetch_nih_reporter(entity_name),
            self.fetch_openalex(entity_name)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        signals = []
        for res in results:
            if isinstance(res, list):
                signals.extend(res)
                
        return signals

async def gather_intelligence(entity_name: str) -> List[CrossReference]:
    """Gather all cross-reference intelligence for an entity."""
    client = IntelligenceClient()
    return await client.fetch_signals(entity_name)
