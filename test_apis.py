import asyncio

import httpx


async def test():
    query = "lithium solid state battery"
    async with httpx.AsyncClient(timeout=10.0) as client:
        # arXiv
        r = await client.get(f"http://export.arxiv.org/api/query?search_query=all:%22{query}%22&max_results=1")
        print("arXiv:", r.status_code)

        # NIH
        r = await client.post("https://api.reporter.nih.gov/v2/projects/search", json={"criteria": {"advanced_text_search": {"operator": "and", "search_terms": [query]}}})
        print("NIH:", r.status_code)

        # NSF
        r = await client.get(f"https://api.nsf.gov/services/v1/awards.json?keyword=%22{query}%22")
        print("NSF:", r.status_code)

        # DOE
        r = await client.get(f"https://www.osti.gov/api/v1/records?q=%22{query}%22")
        print("DOE:", r.status_code)

asyncio.run(test())
