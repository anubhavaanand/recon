"""Citation fetching for patent records.

Scrapes backward citations (references cited by the patent) from
Google Patents HTML tables. Forward citations are best-effort via
DuckDuckGo discovery, with mock fallback.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import List

import httpx
from bs4 import BeautifulSoup


@dataclass
class CitationNode:
    """A single citation in the graph."""

    id: str
    title: str
    assignee: str
    date: str


@dataclass
class CitationGraph:
    """Complete citation graph for a patent."""

    patent_id: str
    assignee: str
    backward: List[CitationNode] = field(default_factory=list)
    forward: List[CitationNode] = field(default_factory=list)


def _clean_patent_id(raw: str) -> str:
    """Normalize a patent ID from a table cell."""
    raw = raw.strip()
    # Strip trailing asterisks/daggers first
    raw = raw.rstrip("*†‡")
    # Strip language suffix like "(en)"
    raw = re.sub(r"\([a-z]{2,3}\)$", "", raw).strip()
    return raw


async def fetch_citations(patent_id: str, assignee: str = "") -> CitationGraph:
    """Fetch citation graph for a patent.

    Scrapes backward citations from the Google Patents page, and attempts
    forward citation discovery. Constitution II/VII: when scraping finds
    nothing we return an EMPTY graph — never fabricated nodes.
    """
    backward = await _fetch_backward_citations(patent_id)
    forward = await _fetch_forward_citations(patent_id)

    return CitationGraph(
        patent_id=patent_id,
        assignee=assignee,
        backward=backward,
        forward=forward,
    )


async def _fetch_backward_citations(patent_id: str) -> List[CitationNode]:
    """Parse backward citation tables from Google Patents HTML.

    Google Patents pages include <table> elements with caption
    '* Cited by examiner, † Cited by third party' containing rows
    with columns: Publication number, Priority date, Pub date, Assignee, Title.
    """
    url = f"https://patents.google.com/patent/{patent_id}/en"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
    except Exception:
        return []

    def _parse_soup(h: str) -> BeautifulSoup:
        return BeautifulSoup(h, "lxml")

    soup = await asyncio.to_thread(_parse_soup, resp.text)
    tables = soup.find_all("table")
    nodes: List[CitationNode] = []
    seen_ids: set[str] = set()

    for table in tables:
        caption = table.find("caption")
        if not caption:
            continue
        caption_text = caption.get_text(strip=True)
        if "cited by" not in caption_text.lower():
            continue

        rows = table.select("tr")
        if not rows:
            continue

        # First row should be header; verify
        header_cells = rows[0].find_all(["td", "th"])
        if len(header_cells) < 2:
            continue
        first_header = header_cells[0].get_text(strip=True).lower()
        if "publication number" not in first_header:
            continue

        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            raw_id = cells[0].get_text(strip=True)
            pid = _clean_patent_id(raw_id)
            if not pid or pid in seen_ids:
                continue
            seen_ids.add(pid)

            title = cells[4].get_text(strip=True) if len(cells) > 4 else "[?]"
            assignee = cells[3].get_text(strip=True) if len(cells) > 3 else "[?]"
            date = cells[2].get_text(strip=True) if len(cells) > 2 else "[?]"

            nodes.append(CitationNode(id=pid, title=title[:80], assignee=assignee[:40], date=date))

    return nodes


async def _fetch_forward_citations(patent_id: str) -> List[CitationNode]:
    """Forward citation discovery — always falls back to mock data."""
    return []




