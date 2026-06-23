import asyncio
from core.models import PatentRecord
from core.enrichment import enrich_patent
async def test():
    rec = PatentRecord(id="AEROX12345", title="aeroplane engine solid state", assignee="Boeing", dates={}, abstract="Test", claims=[], image_urls=[], status="ACTIVE", family_id="")
    await enrich_patent(rec)
    print(rec.cross_references)
asyncio.run(test())
