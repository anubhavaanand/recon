import asyncio

from core.enrichment import _search_signal


async def main():
    res = await _search_signal("sec", "site:sec.gov", "gun")
    print(res)
asyncio.run(main())
