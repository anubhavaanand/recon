"""Cross-reference enrichment via DuckDuckGo discovery.

For each patent, searches intelligence sources (NIH, SEC, arXiv, OpenCorporates)
to find evidence of grant funding, corporate filings, academic citations, and
supply chain connections. These populate PatentRecord.cross_references which
the scoring engine uses to calculate signal scores.
"""

from __future__ import annotations

import asyncio
import re
from typing import Optional

from ddgs import DDGS

from core.models import PatentRecord, CrossReference
from storage.cache import CacheDatabase


# Signal categories mapped to DuckDuckGo site: domains
_SIGNAL_DOMAINS = {
    "nih": "site:reporter.nih.gov",
    "sec": "site:sec.gov",
    "arxiv": "site:arxiv.org",
    "opencorporates": "site:opencorporates.com",
    "nsf": "site:nsf.gov/awardsearch",
    "doe": "site:osti.gov OR site:energy.gov",
}

# Words to skip when building a fallback query from title
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "with", "for",
    "to", "is", "on", "by", "at", "from", "as", "that", "its",
})


_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _extract_date(text: str) -> Optional[str]:
    """Extract the first ISO-format date from a string."""
    if not text:
        return None
    m = _DATE_RE.search(text)
    return m.group(1) if m else None


async def _search_signal(source: str, domain_query: str, search_term: str) -> Optional[CrossReference]:
    """Run a DDGS search for a single signal category. Runs in thread pool."""
    try:
        def _do_search() -> Optional[CrossReference]:
            with DDGS() as ddgs:
                results = list(ddgs.text(f'{domain_query} "{search_term}"', max_results=1))
                if results:
                    r = results[0]
                    snippet = r.get("body", "")
                    return CrossReference(
                        source=source,
                        url=r.get("href", ""),
                        date=_extract_date(snippet),
                        metadata={
                            "title": r.get("title", ""),
                            "snippet": snippet,
                        },
                    )
            return None

        return await asyncio.to_thread(_do_search)
    except Exception:
        return None


def _build_search_query(record: PatentRecord) -> Optional[str]:
    """Determine the search string for enrichment.

    Uses assignee if available; otherwise extracts meaningful words from title.
    Returns None if no usable terms exist.
    """
    assignee = record.assignee
    if assignee and assignee not in ("[?]", "UNKNOWN", ""):
        return assignee

    # Fall back to title words, skipping stop words
    words = [w for w in record.title.split() if w.lower() not in _STOP_WORDS]
    if words:
        return " ".join(words[:5])

    return None


async def enrich_patent(record: PatentRecord) -> PatentRecord:
    """Add cross-reference signals via DuckDuckGo discovery. Non-blocking.

    For each signal category, searches DDGS for the assignee or title.
    If results found, creates a CrossReference and appends to record.
    If DDGS fails or times out, silently returns the original record unchanged.
    """
    try:
        db = CacheDatabase()
        cached = db.get_enrichment_cache(record.id)
        if cached is not None:
            record.cross_references = cached
            return record

        query = _build_search_query(record)
        if not query:
            return record

        # Search all signal domains concurrently
        tasks = [
            _search_signal(source, domain, query)
            for source, domain in _SIGNAL_DOMAINS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        cross_refs = [r for r in results if isinstance(r, CrossReference)]

        if cross_refs:
            record.cross_references = cross_refs
            db.save_enrichment_cache(record.id, cross_refs)

        return record
    except Exception:
        return record
