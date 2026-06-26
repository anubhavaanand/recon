"""Cross-reference enrichment via native research APIs.

For each patent, searches intelligence sources (arXiv, NSF, DOE, NIH, SEC)
to find evidence of grant funding, academic citations, and corporate filings.
These populate PatentRecord.cross_references which the scoring engine uses
to calculate signal scores.
"""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

from core.models import CrossReference, PatentRecord
from storage.cache import CacheDatabase

_SIGNAL_DOMAINS: dict[str, str] = {
    "nih": "NIH RePORTER (grants)",
    "sec": "SEC EDGAR (filings)",
    "arxiv": "arXiv (academic papers)",
    "nsf": "NSF (grants)",
    "doe": "DOE OSTI (research)",
    "openalex": "OpenAlex (publications)",
    "crossref": "Crossref (citations)",
}

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
        url = f'https://export.arxiv.org/api/query?search_query=all:"{query}"&max_results=1'
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entry = root.find('atom:entry', ns)
                if entry is not None:
                    title_el = entry.find('atom:title', ns)
                    summary_el = entry.find('atom:summary', ns)
                    id_el = entry.find('atom:id', ns)
                    published_el = entry.find('atom:published', ns)
                    title = title_el.text if title_el is not None else None
                    summary = summary_el.text if summary_el is not None else None
                    id_url = id_el.text if id_el is not None else None
                    published = published_el.text if published_el is not None else None
                    return CrossReference(
                        source="arxiv",
                        url=id_url or "",
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
        url = f'https://www.osti.gov/api/v1/records?all="{query}"'
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

async def _search_nih(query: str) -> Optional[CrossReference]:
    try:
        url = "https://api.reporter.nih.gov/v2/projects/search"
        payload = {"criteria": {"advanced_text_search": {"operator": "and", "search_text": query}}}
        async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "RECON/1.0"}) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    proj = results[0]
                    raw_date = proj.get("award_notice_date") or ""
                    date = raw_date[:10] if raw_date else None
                    return CrossReference(
                        source="nih",
                        url=f"https://reporter.nih.gov/project-details/{proj.get('core_project_num')}",
                        date=date,
                        metadata={"title": proj.get("project_title", ""), "snippet": proj.get("abstract_text", "")[:200]}
                    )
    except Exception:
        pass
    return None

async def _search_sec(query: str) -> Optional[CrossReference]:
    try:
        url = f"https://efts.sec.gov/LATEST/search-index?q={query}"
        headers = {
            "User-Agent": "RECON Research Tool recon@example.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "efts.sec.gov"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                if hits:
                    doc = hits[0]
                    src = doc.get("_source", {})
                    ciks = src.get("ciks", [])
                    cik = ciks[0] if ciks else ""
                    return CrossReference(
                        source="sec",
                        url=f"https://www.sec.gov/edgar/browse/?CIK={cik}",
                        date=src.get("file_date", ""),
                        metadata={"title": src.get("display_names", [""])[0], "snippet": ""}
                    )
    except Exception:
        pass
    return None

async def _search_openalex(query: str) -> Optional[CrossReference]:
    try:
        url = f"https://api.openalex.org/works?search={query}&per_page=1&mailto=recon@example.com"
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    work = results[0]
                    return CrossReference(
                        source="openalex",
                        url=work.get("doi") or work.get("id", ""),
                        date=work.get("publication_date", ""),
                        metadata={"title": work.get("title", ""), "snippet": ""}
                    )
    except Exception:
        pass
    return None

async def _search_crossref(query: str) -> Optional[CrossReference]:
    try:
        url = f"https://api.crossref.org/works?query={query}&select=DOI,title,author,created&rows=1&mailto=recon@example.com"
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                if items:
                    item = items[0]
                    doi = item.get("DOI", "")
                    title = item.get("title", [""])[0] if item.get("title") else ""
                    return CrossReference(
                        source="crossref",
                        url=f"https://doi.org/{doi}" if doi else "",
                        date="",  # Crossref dates are nested arrays, skipping for brevity
                        metadata={"title": title, "snippet": ""}
                    )
    except Exception:
        pass
    return None

def _build_search_query(record: PatentRecord) -> Optional[str]:
    assignee = record.assignee
    if assignee and assignee not in ("[?]", "UNKNOWN", ""):
        # If the assignee string is too long, it's probably garbage/boilerplate
        if len(assignee) < 30:
            return assignee

    # Fall back to title words
    words = [w for w in record.title.split() if w.lower() not in _STOP_WORDS]
    if words:
        return " ".join(words[:4])
    return None

async def enrich_patent(record: PatentRecord) -> PatentRecord:
    try:
        db = CacheDatabase()
        cached = db.get_enrichment_cache(record.id)
        if cached: # only return if there are actual items
            record.cross_references = cached
            return record

        query = _build_search_query(record)
        if not query:
            return record

        tasks = [
            _search_arxiv(query),
            _search_nsf(query),
            _search_doe(query),
            _search_nih(query),
            _search_sec(query),
            _search_openalex(query),
            _search_crossref(query),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        cross_refs = [r for r in results if isinstance(r, CrossReference)]

        if cross_refs:
            record.cross_references = cross_refs
            db.save_enrichment_cache(record.id, cross_refs)

        return record
    except Exception:
        return record
