import asyncio

import httpx


async def test():
    query = "lithium battery"
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Crossref
        url_cr = f"https://api.crossref.org/works?query={query}&select=DOI,title,author&rows=1&mailto=recon@example.com"
        r1 = await client.get(url_cr)
        print("Crossref:", r1.status_code)

        # OpenAlex
        url_oa = f"https://api.openalex.org/works?search={query}&per_page=1&mailto=recon@example.com"
        r2 = await client.get(url_oa)
        print("OpenAlex:", r2.status_code)

asyncio.run(test())
