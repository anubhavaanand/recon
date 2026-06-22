"""Citation fetching for patent records.

Scrapes backward citations (references cited by the patent) from
Google Patents HTML tables. Forward citations are best-effort via
DuckDuckGo discovery, with mock fallback.
"""

from __future__ import annotations

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
    forward citation discovery via DDGS. Falls back gracefully.
    """
    backward = await _fetch_backward_citations(patent_id)
    forward = await _fetch_forward_citations(patent_id)

    if not backward and not forward:
        backward = _mock_backward(patent_id)
        forward = _mock_forward(patent_id)

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

    soup = BeautifulSoup(resp.text, "lxml")
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
    """Attempt forward citation discovery via DDGS.

    Searches for the patent number on Google Patents to find
    other patents that cite it.
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"site:patents.google.com \"{patent_id}\" cited by",
                max_results=8,
            ))
    except Exception:
        return []

    nodes: List[CitationNode] = []
    seen_ids: set[str] = set()

    for r in results:
        href = r.get("href", "")
        if "patents.google.com/patent/" not in href:
            continue
        pid_match = re.search(r"/patent/([A-Za-z0-9]+)", href)
        if not pid_match:
            continue
        pid = pid_match.group(1)
        if pid == patent_id or pid in seen_ids:
            continue

        # Try to fetch the page for richer data
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(href, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    page_soup = BeautifulSoup(resp.text, "lxml")
                    title_el = page_soup.find("title")
                    title = title_el.get_text(strip=True) if title_el else "[?]"
                    title = re.sub(r"\s*-\s*Google Patents$", "", title)
                else:
                    title = r.get("title", "[?]")
        except Exception:
            title = r.get("title", "[?]")

        seen_ids.add(pid)
        nodes.append(CitationNode(id=pid, title=title[:80], assignee="[?]", date="[?]"))

    return nodes


def _mock_backward(patent_id: str) -> List[CitationNode]:
    """Mock backward citations for demo/testing."""
    return [
        CitationNode(id=f"US10000001B2", title="Prior art battery technology", assignee="Samsung", date="2018-03-01"),
        CitationNode(id=f"WO2020000001A1", title="Electrolyte compositions", assignee="Toyota", date="2020-01-15"),
        CitationNode(id=f"EP35000001B1", title="Solid state cell architecture", assignee="BASF", date="2019-06-20"),
        CitationNode(id=f"JP2018000001A", title="Ceramic separator method", assignee="Panasonic", date="2018-11-10"),
        CitationNode(id=f"CN109000001A", title="Lithium anode protection", assignee="CATL", date="2019-04-05"),
    ]


def _mock_forward(patent_id: str) -> List[CitationNode]:
    """Mock forward citations for demo/testing."""
    return [
        CitationNode(id=f"US20230000001A1", title="Advanced battery management", assignee="Tesla", date="2023-01-10"),
        CitationNode(id=f"EP41000001A1", title="Next-gen solid electrolyte", assignee="QuantumScape", date="2022-08-15"),
        CitationNode(id=f"WO2023000001A1", title="High energy density cell", assignee="LG Chem", date="2023-05-20"),
    ]
