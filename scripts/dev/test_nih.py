import asyncio

import httpx


async def test():
    query = "lithium battery"
    url = "https://api.reporter.nih.gov/v2/projects/search"
    payload = {"criteria": {"advanced_text_search": {"operator": "and", "search_terms": [query]}}}
    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "RECON/1.0"}) as client:
        resp = await client.post(url, json=payload)
        print("NIH Status:", resp.status_code)

asyncio.run(test())
