import asyncio
import logging
import re
from typing import List, Optional
from core.models import PatentRecord
from clients.patent_apis import USPTOClient, EPOClient, WIPOClient, LensClient, GooglePatentsClient, PatsnapClient
from clients.circuit_breaker import CircuitOpenError
from storage.cache import CacheDatabase

logger = logging.getLogger("recon")

_SHELL_CHARS_RE = re.compile(r'[;|&$`(){}\[\]<>#~!\\]')
_CQL_WILDCARD_ALL_RE = re.compile(r'\*:\*')
_MULTI_SPACE_RE = re.compile(r' {2,}')


def sanitize_query(query: str) -> str:
    """
    Sanitize a user query before passing to external services.

    Removes shell metacharacters and CQL injection patterns to prevent
    command injection and search-engine query injection. Preserves
    alphanumerics, spaces, quotes, hyphens, colons, slashes, and periods
    needed for patent search syntax.
    """
    query = _SHELL_CHARS_RE.sub("", query)
    query = _CQL_WILDCARD_ALL_RE.sub("", query)
    query = _MULTI_SPACE_RE.sub(" ", query)
    query = query.strip()
    return query

_SAFE_MODE_ACTIVE = False


def is_safe_mode() -> bool:
    return _SAFE_MODE_ACTIVE


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

    When circuit breakers trip, degrades to Safe Mode: returns cache-only
    results without crashing.

    Args:
        query: Search query string.
        sources: List of source names to include (e.g. ["uspto", "epo"]).
                 Defaults to all sources if None.
    """
    global _SAFE_MODE_ACTIVE

    query = sanitize_query(query)

    db = CacheDatabase()
    cached = db.get_cached_search(query)
    if cached:
        return sort_and_merge_results(cached)

    from clients.patentsview import search_patentsview
    tasks = []

    if sources is None or "uspto" in sources:
        tasks.append(search_patentsview(query))

    other_sources = [s for s in (sources or ALL_SOURCES) if s != "uspto"]
    clients = []

    for src in other_sources:
        src_lower = src.strip().lower()
        entry = SOURCE_REGISTRY.get(src_lower)
        if entry is None:
            print(f"WARN: Unknown source '{src}' — skipped. Valid: {', '.join(ALL_SOURCES)}")
            continue
        _, cls = entry
        clients.append(cls())

    for client in clients:
        tasks.append(client.search(query))

    if not tasks:
        return []

    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    all_records = []
    circuit_triggered = False
    for res in results_nested:
        if isinstance(res, list):
            all_records.extend(res)
        elif isinstance(res, CircuitOpenError):
            circuit_triggered = True
            logger.warning("Circuit breaker tripped during search", extra={"component": "search", "event": "circuit_open"})
            print("WARN: Source unavailable (circuit breaker open). Falling back to cache.")
        elif isinstance(res, Exception):
            print(f"ERR: Search source failed: {res}")

    merged = sort_and_merge_results(all_records)

    if circuit_triggered:
        _SAFE_MODE_ACTIVE = True
        stale = _get_stale_cache(db, query)
        if stale:
            merged = sort_and_merge_results(stale)
            print("WARN: SAFE MODE — serving stale cached results. Live sources may be blocked.")
            logger.warning("Safe mode activated — serving stale cache", extra={"component": "search", "event": "safe_mode"})

    if merged and not circuit_triggered:
        db.save_search_results(query, merged)

    return merged


def _get_stale_cache(db: CacheDatabase, query: str) -> Optional[List[PatentRecord]]:
    from storage.cache import _query_hash
    import json
    from core.models import CrossReference

    qhash = _query_hash(query)
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT results_json FROM search_results WHERE query_hash = ?",
            (qhash,),
        ).fetchone()

    if not row:
        return None

    data_list = json.loads(row["results_json"])
    records = []
    for data_dict in data_list:
        if "cross_references" in data_dict:
            data_dict["cross_references"] = [
                CrossReference(**cr) for cr in data_dict["cross_references"]
            ]
        records.append(PatentRecord(**data_dict))
    return records if records else None
