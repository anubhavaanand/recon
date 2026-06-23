import asyncio
from core.models import PatentRecord
from core.enrichment import enrich_patent

async def test():
    rec = PatentRecord(id="EP23159626", title="lithium batteries", assignee="SK On Co., Ltd.", dates={}, abstract="Test", claims=[], image_urls=[], status="ACTIVE", family_id="")
    await enrich_patent(rec)
    print("Cross references found:", len(rec.cross_references))
    for c in rec.cross_references:
        print(c.source, c.url)

asyncio.run(test())
