import asyncio
from core.models import PatentRecord
from core.enrichment import enrich_patent
async def test():
    rec = PatentRecord(id="US1000000B2", title="Aeroplane engine", assignee="Boeing", dates={}, abstract="Test", claims=[], image_urls=[], status="ACTIVE", family_id="")
    await enrich_patent(rec)
    print(rec.cross_references)
asyncio.run(test())
