from typing import List
from clients.base import BaseAsyncClient
from core.models import PatentRecord

class USPTOClient(BaseAsyncClient):
    async def search(self, query: str) -> List[PatentRecord]:
        # TODO: Implement real USPTO API call. Returning mock for now.
        return [PatentRecord(id="US123", title=f"USPTO {query}", assignee="Mock Assignee", dates={"filed": "2020-01-01"}, abstract="Mock abstract", claims=[], image_urls=[], status="active", family_id="F123")]

class EPOClient(BaseAsyncClient):
    async def search(self, query: str) -> List[PatentRecord]:
        return [PatentRecord(id="EP123", title=f"EPO {query}", assignee="Mock Assignee", dates={"filed": "2020-01-02"}, abstract="Mock abstract", claims=[], image_urls=[], status="active", family_id="F123")]

class WIPOClient(BaseAsyncClient):
    async def search(self, query: str) -> List[PatentRecord]:
        return [PatentRecord(id="WO123", title=f"WIPO {query}", assignee="Mock Assignee", dates={"filed": "2020-01-03"}, abstract="Mock abstract", claims=[], image_urls=[], status="active", family_id="F123")]

class LensClient(BaseAsyncClient):
    async def search(self, query: str) -> List[PatentRecord]:
        return [PatentRecord(id="LENS123", title=f"Lens {query}", assignee="Mock Assignee", dates={"filed": "2020-01-04"}, abstract="Mock abstract", claims=[], image_urls=[], status="active", family_id="F123")]

class GooglePatentsClient(BaseAsyncClient):
    async def search(self, query: str) -> List[PatentRecord]:
        return [PatentRecord(id="GOOG123", title=f"Google {query}", assignee="Mock Assignee", dates={"filed": "2020-01-05"}, abstract="Mock abstract", claims=[], image_urls=[], status="active", family_id="F123")]
