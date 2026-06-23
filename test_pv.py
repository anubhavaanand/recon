import asyncio
import httpx

async def test():
    query = "lithium battery"
    url = "https://api.patentsview.org/patents/query"
    payload = {
        "q": {"_text_any": {"patent_abstract": query}},
        "f": ["patent_number", "patent_title", "patent_abstract", "patent_date", "assignee_organization"],
        "o": {"per_page": 5},
        "s": [{"patent_date": "desc"}]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        print("Status:", resp.status_code)
        print("Headers:", resp.headers)

asyncio.run(test())
