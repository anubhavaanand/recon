import asyncio
from typing import List
from core.models import PatentRecord
from clients.patent_apis import USPTOClient, EPOClient, WIPOClient, LensClient, GooglePatentsClient

def sort_and_merge_results(records: List[PatentRecord]) -> List[PatentRecord]:
    """
    Sorts descending by filed date, never dropping any entry.
    """
    def get_sort_key(record: PatentRecord) -> str:
        # Default to very old date if filed date is unknown or missing
        return record.dates.get("filed", "0000-00-00")
        
    # Python's list.sort is stable and we want descending
    return sorted(records, key=get_sort_key, reverse=True)

async def search_all(query: str) -> List[PatentRecord]:
    """
    Fetches results concurrently from all configured clients and merges them.
    """
    clients = [
        USPTOClient(),
        EPOClient(),
        WIPOClient(),
        LensClient(),
        GooglePatentsClient(),
    ]
    
    # We will close the clients properly if they were real, 
    # for now we instantiate here for the concurrent fetch.
    tasks = [client.search(query) for client in clients]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_records = []
    for res in results_nested:
        if isinstance(res, list):
            all_records.extend(res)
        elif isinstance(res, Exception):
            # We log dry errors, but do not fail the whole search
            print(f"ERR: Search source failed: {res}")
            
    return sort_and_merge_results(all_records)
