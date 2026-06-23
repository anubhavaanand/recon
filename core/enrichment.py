"""Cross-reference enrichment via native APIs and DuckDuckGo.

For each patent, searches intelligence sources (NIH, SEC, arXiv, OpenCorporates)
to find evidence of grant funding, corporate filings, academic citations, and
supply chain connections. These populate PatentRecord.cross_references which
the scoring engine uses to calculate signal scores.
"""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from typing import Optional

import httpx
from ddgs import DDGS

from core.models import PatentRecord, CrossReference
from storage.cache import CacheDatabase


_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "with", "for",
    "to", "is", "on", "by", "at", "from", "as", "that", "its",
})

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

def _extract_date(text: str) -> Optional[str]:
    if not text:
        return None
    m = _DATE_RE.search(text)
    return m.group(1) if m else None

async def _search_arxiv(query: str) -> Optional[CrossReference]:
    try:
        url = f'http://export.arxiv.org/api/query?search_query=all:"{query}"&max_results=1'
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entry = root.find('atom:entry', ns)
                if entry is not None:
                    title = entry.find('atom:title', ns).text
                    summary = entry.find('atom:summary', ns).text
                    id_url = entry.find('atom:id', ns).text
                    published = entry.find('atom:published', ns).text
                    return CrossReference(
                        source="arxiv",
                        url=id_url,
                        date=published[:10] if published else None,
                        metadata={"title": title.strip().replace("\n", " ") if title else "", "snippet": summary[:200] if summary else ""}
                    )
    except Exception:
        pass
    return None

async def _search_nsf(query: str) -> Optional[CrossReference]:
    try:
        url = f'https://api.nsf.gov/services/v1/awards.json?keyword="{query}"'
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                awards = data.get("response", {}).get("award", [])
                if awards:
                    award = awards[0]
                    return CrossReference(
                        source="nsf",
                        url=f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={award.get('id')}",
                        date=award.get("date"),
                        metadata={"title": award.get("title", ""), "snippet": award.get("abstractText", "")[:200]}
                    )
    except Exception:
        pass
    return None

async def _search_doe(query: str) -> Optional[CrossReference]:
    try:
        url = f'https://www.osti.gov/api/v1/records?q="{query}"'
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list):
                    record = data[0]
                    return CrossReference(
                        source="doe",
                        url=f"https://www.osti.gov/biblio/{record.get('osti_id')}",
                        date=record.get("publication_date"),
                        metadata={"title": record.get("title", ""), "snippet": record.get("description", "")[:200]}
                    )
    except Exception:
        pass
    return None

async def _search_ddg_signal(source: str, domain_query: str, search_term: str) -> Optional[CrossReference]:
    try:
        from clients.scrapers import _ddg_search
        import urllib.parse
        results = await _ddg_search(f'{domain_query} "{search_term}"', max_results=1)
        if results:
            r = results[0]
            snippet = r.get("body", "")
            href = r.get("href", "")
            if "duckduckgo.com/l/" in href and "uddg=" in href:
                parsed = urllib.parse.urlparse(href)
                qs = urllib.parse.parse_qs(parsed.query)
                if "uddg" in qs:
                    href = qs["uddg"][0]
            return CrossReference(
                source=source,
                url=href,
                date=_extract_date(snippet),
                metadata={"title": r.get("title", ""), "snippet": snippet}
            )
    except Exception:
        pass
    return None

def _build_search_query(record: PatentRecord) -> Optional[str]:
    assignee = record.assignee
    if assignee and assignee not in ("[?]", "UNKNOWN", ""):
        return assignee
    words = [w for w in record.title.split() if w.lower() not in _STOP_WORDS]
    if words:
        return " ".join(words[:5])
    return None

async def enrich_patent(record: PatentRecord) -> PatentRecord:
    try:
        db = CacheDatabase()
        cached = db.get_enrichment_cache(record.id)
        if cached is not None:
            record.cross_references = cached
            return record

        query = _build_search_query(record)
        if not query:
            return record

        tasks = [
            _search_arxiv(query),
            _search_nsf(query),
            _search_doe(query),
            _search_ddg_signal("sec", "site:sec.gov", query),
            _search_ddg_signal("opencorporates", "site:opencorporates.com", query),
            _search_ddg_signal("nih", "site:reporter.nih.gov", query),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        cross_refs = [r for r in results if isinstance(r, CrossReference)]

        if cross_refs:
            record.cross_references = cross_refs
            db.save_enrichment_cache(record.id, cross_refs)

        return record
    except Exception:
        return record
