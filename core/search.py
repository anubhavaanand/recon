import asyncio
from typing import List, Optional
from core.models import PatentRecord
from clients.patent_apis import USPTOClient, EPOClient, WIPOClient, LensClient, GooglePatentsClient, PatsnapClient
from storage.cache import CacheDatabase

# Source registry: maps short name -> (display name, class)
SOURCE_REGISTRY: dict[str, tuple[str, type]] = {
    "uspto": ("USPTO", USPTOClient),
    "epo": ("EPO", EPOClient),
    "wipo": ("WIPO", WIPOClient),
    "lens": ("Lens", LensClient),
    "google": ("GooglePatents", GooglePatentsClient),
    "patsnap": ("PatSnap", PatsnapClient),
}

ALL_SOURCES = list(SOURCE_REGISTRY.keys())


def sort_key_desc(record: PatentRecord) -> tuple:
    filed = record.dates.get("filed", "")
    is_valid = bool(filed) and filed != "[?]" and filed != "UNKNOWN"
    return (0 if is_valid else 1, filed if is_valid else "")


def sort_and_merge_results(records: List[PatentRecord]) -> List[PatentRecord]:
    """
    Sorts descending by filed date, never dropping any entry.
    Records with missing/invalid dates sort last (after all dated records).
    """
    dated = [r for r in records if sort_key_desc(r)[0] == 0]
    undated = [r for r in records if sort_key_desc(r)[0] == 1]
    dated.sort(key=lambda r: r.dates.get("filed", ""), reverse=True)
    return dated + undated


async def search_all(query: str, sources: Optional[List[str]] = None) -> List[PatentRecord]:
    """
    Fetches results concurrently from selected clients and merges them.
    Checks cache before hitting APIs.

    Args:
        query: Search query string.
        sources: List of source names to include (e.g. ["uspto", "epo"]).
                 Defaults to all sources if None.
    """
    db = CacheDatabase()
    cached = db.get_cached_search(query)
    if cached:
        return sort_and_merge_results(cached)

    if sources is None:
        sources = ALL_SOURCES

    clients = []
    for src in sources:
        src_lower = src.strip().lower()
        entry = SOURCE_REGISTRY.get(src_lower)
        if entry is None:
            print(f"WARN: Unknown source '{src}' — skipped. Valid: {', '.join(ALL_SOURCES)}")
            continue
        _, cls = entry
        clients.append(cls())

    if not clients:
        return []

    tasks = [client.search(query) for client in clients]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    all_records = []
    for res in results_nested:
        if isinstance(res, list):
            all_records.extend(res)
        elif isinstance(res, Exception):
            print(f"ERR: Search source failed: {res}")

    merged = sort_and_merge_results(all_records)
    if merged:
        db.save_search_results(query, merged)

    # Enrich top 5 results with cross-references (Constitution §6: Speed over Depth)
    from core.enrichment import enrich_patent
    top_n = merged[:5]
    enrichment_tasks = [enrich_patent(r) for r in top_n]
    await asyncio.gather(*enrichment_tasks, return_exceptions=True)

    return merged
