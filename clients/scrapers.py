"""Web scrapers for patent sources without official APIs.

Uses ddgs (DuckDuckGo) for discovery, httpx for fetching, and BeautifulSoup
for parsing. These sources are free but fragile -- HTML structure changes may
break parsing. In that case, they gracefully return empty results.
"""

from __future__ import annotations

import asyncio
import re
from typing import List

import httpx
from bs4 import BeautifulSoup

from core.models import PatentRecord


async def _fetch_html(url: str, timeout: float = 15.0) -> str | None:
    """Fetch HTML from a URL using httpx."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            return resp.text
    except Exception:
        return None


def _parse_google_patent_html(html: str) -> dict | None:
    """Parse a single Google Patents page and extract patent fields."""
    soup = BeautifulSoup(html, "lxml")

    pn_el = soup.select_one("[itemprop='publicationNumber'], [data-patent-number]")
    pn = pn_el.get_text(strip=True) if pn_el else None

    if not pn:
        title_tag = soup.find("title")
        if title_tag:
            m = re.search(r"([A-Z]{2}\d+[A-Z0-9]*)", title_tag.get_text())
            if m:
                pn = m.group(1)

    title_el = soup.select_one("[itemprop='title'], h1, .patent-title")
    title = title_el.get_text(strip=True) if title_el else "[?]"

    assignee_el = soup.select_one("[itemprop='assignee'], .assignee, .patent-assignee")
    assignee = assignee_el.get_text(strip=True) if assignee_el else "[?]"

    abstract_el = soup.select_one("[itemprop='abstract'], .abstract, .patent-abstract")
    abstract = abstract_el.get_text(strip=True) if abstract_el else "[?]"

    date_el = soup.select_one("[itemprop='filingDate'], [itemprop='datePublished'], .filing-date, .pub-date")
    filed = date_el.get("content") or date_el.get_text(strip=True) if date_el else "[?]"
    if filed and filed != "[?]":
        filed = filed[:10]

    status_el = soup.select_one("[itemprop='status'], .status, .legal-status")
    status = status_el.get_text(strip=True) if status_el else "UNKNOWN"

    return {
        "id": pn or "UNKNOWN",
        "title": title,
        "assignee": assignee,
        "abstract": abstract,
        "dates": {"filed": filed} if filed != "[?]" else {},
        "status": status[:20],
    }


def _parse_wipo_patent_html(html: str) -> dict | None:
    """Parse a single WIPO PATENTSCOPE page."""
    soup = BeautifulSoup(html, "lxml")

    pn_el = soup.select_one(".patent-number, .publication-number, [id*='pubNumber']")
    pn = pn_el.get_text(strip=True) if pn_el else None

    if not pn:
        m = re.search(r"(WO\d{4}\d+)", html)
        if m:
            pn = m.group(1)

    title_el = soup.select_one(".title, .invention-title, h1")
    title = title_el.get_text(strip=True) if title_el else "[?]"

    assignee_el = soup.select_one(".applicant, .assignee, [id*='applicant']")
    assignee = assignee_el.get_text(strip=True) if assignee_el else "[?]"

    abstract_el = soup.select_one(".abstract, [id*='abstract']")
    abstract = abstract_el.get_text(strip=True) if abstract_el else "[?]"

    return {
        "id": pn or "UNKNOWN",
        "title": title,
        "assignee": assignee,
        "abstract": abstract,
        "dates": {},
        "status": "UNKNOWN",
    }


async def _fetch_patents_from_urls(urls: list[str], parser_fn, timeout: float = 8.0) -> list[PatentRecord]:
    """Fetch patent pages concurrently and parse them."""
    seen_ids: set[str] = set()
    records: list[PatentRecord] = []

    async def _fetch_and_parse(url: str) -> PatentRecord | None:
        html = await _fetch_html(url, timeout=timeout)
        if not html:
            return None
        parsed = parser_fn(html)
        if not parsed:
            return None

        pid = parsed["id"]
        if pid in seen_ids:
            return None
        seen_ids.add(pid)

        if not parsed.get("dates"):
            parsed["dates"] = {"filed": "[?]"}
        if not parsed.get("status"):
            parsed["status"] = "UNKNOWN"

        return PatentRecord(
            id=pid,
            title=parsed["title"],
            assignee=parsed["assignee"],
            dates=parsed["dates"],
            abstract=parsed["abstract"],
            claims=[],
            image_urls=[],
            status=parsed["status"],
            family_id="UNKNOWN",
        )

    tasks = [_fetch_and_parse(u) for u in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, PatentRecord):
            records.append(r)
    return records


async def search_google_patents(query: str) -> List[PatentRecord]:
    """Search Google Patents via DuckDuckGo discovery + HTML scraping."""
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(f"site:patents.google.com {query}", max_results=5))
    except Exception:
        return []

    urls = []
    for r in results:
        href = r.get("href", "")
        if "patents.google.com/patent/" in href:
            urls.append(href)

    return await _fetch_patents_from_urls(urls, _parse_google_patent_html)


async def search_wipo_patents(query: str) -> List[PatentRecord]:
    """Search WIPO PATENTSCOPE via DuckDuckGo snippet data.

    WIPO PATENTSCOPE uses JSF (JavaScript Faces) for rendering, so scraping
    the HTML directly yields empty data. Instead we use DuckDuckGo search
    result snippets which include title, description, and patent number.
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(f"site:patentscope.wipo.int {query}", max_results=5))
    except Exception:
        return []

    records: list[PatentRecord] = []
    seen_ids: set[str] = set()

    # Try fetching individual patent pages concurrently for richer data
    patent_urls = []
    for r in results:
        href = r.get("href", "")
        if "patentscope.wipo.int" not in href:
            continue
        title_lower = (r.get("title") or "").lower()
        if any(kw in title_lower for kw in ["passkey", "sign in", "log in", "register", "create account"]):
            continue
        patent_urls.append(href)

    # If we found patent page URLs, fetch and parse them
    if patent_urls:
        page_records = await _fetch_patents_from_urls(
            patent_urls, _parse_wipo_patent_html, timeout=6.0
        )
        if page_records:
            return page_records

    for r in results:
        href = r.get("href", "")
        if "patentscope.wipo.int" not in href:
            continue

        # Skip non-patent pages
        title_lower = (r.get("title") or "").lower()
        if any(kw in title_lower for kw in ["passkey", "sign in", "log in", "register", "create account"]):
            continue

        # Extract patent number from URL or title
        title_raw = r.get("title", "")
        snippet = r.get("body", "")

        pid = None
        m = re.search(r"/WO([2-9]\d{3,}/\d+)", href.replace("-", ""))
        if m:
            pid = "WO" + m.group(1).replace("/", "")
        m2 = re.search(r"(WO[2-9]\d{7,})", title_raw)
        if not pid and m2:
            pid = m2.group(1)
        if not pid:
            m3 = re.search(r"(WO[2-9]\d{7,})", href)
            if m3:
                pid = m3.group(1)
        if not pid:
            continue

        if pid in seen_ids:
            continue
        seen_ids.add(pid)

        # Clean title — strip leading patent ID prefix
        title = title_raw.strip() if title_raw else "[?]"
        for prefix in [pid, pid.replace("WO", "WO/"), pid.replace("WO", "Wo/")]:
            if title.startswith(prefix):
                title = title[len(prefix):].strip().lstrip("- ")
        if not title:
            title = "[?]"

        abstract = snippet.strip() if snippet else "[?]"

        # Try to fetch the detail page to get publication date
        filed = "[?]"
        try:
            html = await _fetch_html(href, timeout=6.0)
            if html:
                soup = BeautifulSoup(html, "lxml")
                date_el = soup.select_one("[id*='pubDate'], [id*='pubDate'], .publication-date, .date")
                if date_el:
                    d = date_el.get_text(strip=True)[:10]
                    if d:
                        filed = d
        except Exception:
            pass

        records.append(PatentRecord(
            id=pid,
            title=title,
            assignee="[?]",
            dates={"filed": filed},
            abstract=abstract,
            claims=["[?]"],
            image_urls=["[?]"],
            status="UNKNOWN",
            family_id="UNKNOWN",
        ))

    return records


async def search_lens_patents(query: str) -> List[PatentRecord]:
    """Search Lens.org via DuckDuckGo snippet data.

    Lens.org patent pages are JS-rendered and not accessible via httpx scraping.
    We use DDGS search result snippets to extract patent numbers and titles.
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(f"site:lens.org/lens/patent {query}", max_results=5))
    except Exception:
        return []

    records: list[PatentRecord] = []
    seen_ids: set[str] = set()

    for r in results:
        href = r.get("href", "")
        if "lens.org/lens/patent/" not in href:
            continue

        title_raw = r.get("title", "")
        snippet = r.get("body", "")

        # Extract Lens patent ID from URL: /lens/patent/XXX-XXX-XXX-XXX-XXX
        pid = None
        m = re.search(r"/lens/patent/([\w-]+)", href)
        if m:
            pid = m.group(1)

        if not pid or pid in seen_ids:
            continue
        seen_ids.add(pid)

        title = title_raw.strip() if title_raw else "[?]"
        abstract = snippet.strip() if snippet else "[?]"

        records.append(PatentRecord(
            id=pid,
            title=title,
            assignee="[?]",
            dates={"filed": "[?]"},
            abstract=abstract,
            claims=["[?]"],
            image_urls=["[?]"],
            status="UNKNOWN",
            family_id="UNKNOWN",
        ))

    return records


async def search_epo_patents(query: str) -> List[PatentRecord]:
    """Search EPO Register via DuckDuckGo snippet data.

    EPO register and Espacenet pages are behind Cloudflare and not accessible
    via httpx scraping. We use DDGS search result snippets to extract patent
    numbers and titles.
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(f"site:register.epo.org {query}", max_results=5))
    except Exception:
        return []

    records: list[PatentRecord] = []
    seen_ids: set[str] = set()

    for r in results:
        href = r.get("href", "")
        if "register.epo.org" not in href:
            continue

        title_raw = r.get("title", "")
        snippet = r.get("body", "")

        # Extract patent number from URL
        pid = None
        m = re.search(r"(EP\d{7,})", href)
        if m:
            pid = m.group(1)
        m2 = re.search(r"(EP\d{7,})", title_raw)
        if not pid and m2:
            pid = m2.group(1)
        if not pid:
            m3 = re.search(r"application.number=(\w+)", href)
            if m3:
                pid = m3.group(1)

        if not pid or pid in seen_ids:
            continue
        seen_ids.add(pid)

        title = title_raw.strip() if title_raw else "[?]"
        abstract = snippet.strip() if snippet else "[?]"

        records.append(PatentRecord(
            id=pid,
            title=title,
            assignee="[?]",
            dates={"filed": "[?]"},
            abstract=abstract,
            claims=["[?]"],
            image_urls=["[?]"],
            status="UNKNOWN",
            family_id="UNKNOWN",
        ))

    return records
