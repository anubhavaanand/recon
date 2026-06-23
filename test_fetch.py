import asyncio
from clients.scrapers import search_google_patents
async def main():
    res = await search_google_patents("US20260001647A1")
    print(res)
asyncio.run(main())
