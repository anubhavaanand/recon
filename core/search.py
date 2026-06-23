import asyncio
import logging
import re
from typing import List, Optional
from core.models import PatentRecord
from clients.patent_apis import USPTOClient, EPOClient, WIPOClient, LensClient, GooglePatentsClient, PatsnapClient
from storage.cache import CacheDatabase

logger = logging.getLogger("recon")

_SHELL_CHARS_RE = re.compile(r'[;|&$`(){}\[\]<>#~!\\]')
_CQL_WILDCARD_ALL_RE = re.compile(r'\*:\*')
_MULTI_SPACE_RE = re.compile(r' {2,}')
_CONTROL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def sanitize_query(query: str) -> str:
    """
    Sanitize a user query before passing to external services.

    Removes shell metacharacters, null bytes, control characters, and CQL
    injection patterns. Truncates to 500 characters max.
    """
    query = query.replace("\0", "")
    query = _CONTROL_CHARS_RE.sub("", query)
    query = _SHELL_CHARS_RE.sub("", query)
    query = _CQL_WILDCARD_ALL_RE.sub("", query)
    query = _MULTI_SPACE_RE.sub(" ", query)
    query = query.strip()[:500]
    return query

def _check_circuit_breakers(sources: list[str]) -> bool:
    """Returns True if all requested sources have open circuits."""
    try:
        db = CacheDatabase()
        rows = db.get_all_source_health()
        if not isinstance(rows, list):
            return False
        all_open = all(
            row.get("circuit_open", False)
            for row in rows
            if row.get("source_name") in sources
        )
        return bool(rows) and all_open
    except Exception:
        return False


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
    query = sanitize_query(query)

    db = CacheDatabase()
    cached = db.get_cached_search(query)
    if cached:
        return sort_and_merge_results(cached)

    if sources is None:
        sources = ALL_SOURCES

    safe_mode = _check_circuit_breakers(sources)
    if safe_mode:
        stale = _get_stale_cache(db, query)
        if stale:
            logger.warning("Safe mode active. Serving stale cache.")
        else:
            logger.warning("Safe mode active. No cache available.")
        return sort_and_merge_results(stale) if stale else []

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
    errors = 0
    for res in results_nested:
        if isinstance(res, list):
            all_records.extend(res)
        elif isinstance(res, Exception):
            errors += 1
            print(f"ERR: Search source failed: {res}")

    merged = sort_and_merge_results(all_records)

    if errors == len(clients):
        stale = _get_stale_cache(db, query)
        if stale:
            print("ERR: All sources failed. Serving cached results.")
            return sort_and_merge_results(stale)

    if merged:
        db.save_search_results(query, merged)

    return merged


async def semantic_search(query: str, top_k: int = 20) -> list[PatentRecord]:
    """Rerank search results by cosine similarity against stored embeddings.

    Embeds query via nomic-embed-text, computes similarity against all cached
    patent embeddings, returns top_k results. Returns empty list on failure.
    """
    from core.ai import AIProvider, cosine_similarity

    ai = AIProvider()
    query_emb = await ai.generate_embedding(query)
    if not query_emb:
        return []

    db = CacheDatabase()
    all_embs = db.get_all_embeddings()
    if not all_embs:
        return []

    scored: list[tuple[str, float]] = []
    for pid, emb in all_embs.items():
        sim = cosine_similarity(query_emb, emb)
        if sim > 0.0:
            scored.append((pid, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_pids = {pid for pid, _ in scored[:top_k]}

    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT patent_json FROM collections WHERE patent_id IN ({}) ORDER BY saved_at DESC".format(
                ",".join("?" for _ in top_pids)
            ),
            list(top_pids),
        ).fetchall()

    from core.models import CrossReference
    records = []
    for row in rows:
        data = json.loads(row["patent_json"])
        if "cross_references" in data:
            data["cross_references"] = [CrossReference(**cr) for cr in data["cross_references"]]
        records.append(PatentRecord(**data))

    pid_order = {pid: i for i, pid in enumerate(top_pids)}
    records.sort(key=lambda r: pid_order.get(r.id or "", 999))
    return records


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
