import httpx
import asyncio

async def test():
    url = "https://efts.sec.gov/LATEST/search-index?q=battery"
    headers = {
        "User-Agent": "RECON Research Tool admin@recon-tool.org",
        "Accept-Encoding": "gzip, deflate",
        "Host": "efts.sec.gov"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
        print("Status:", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if hits:
                print("Found SEC hits!", len(hits))
                print(hits[0].get("_source", {}).get("display_names", []))
            else:
                print("No hits")

asyncio.run(test())
