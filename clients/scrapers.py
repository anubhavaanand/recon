"""Web scrapers for patent sources without official APIs.

Uses ddgs (DuckDuckGo) for discovery, BaseScraper for resilient fetching,
and BeautifulSoup for parsing. These sources are free but fragile --
HTML structure changes may break parsing. In that case, they gracefully
return empty results.

Resilience (per architecture.md §6.2):
  - Rotating User-Agents (20+ modern browser UA strings)
  - Random jitter (asyncio.sleep(random.uniform(1.0, 3.0)))
  - Max 2 concurrent DDG workers (asyncio.Semaphore(2))
  - Per-source circuit breakers (429 -> fail fast, trip after 3)
  - No exponential backoff -- scrapers fail fast on 429
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import List

import httpx
from bs4 import BeautifulSoup

from clients.base_scraper import BaseScraper, RateLimitedError, SourceDisabledError, _DDG_SEMAPHORE
from clients.circuit_breaker import CircuitBreaker, CircuitOpenError
from core.models import PatentRecord
from core.search import sanitize_query
from urllib.parse import urlparse

logger = logging.getLogger("recon")


def is_clean_url(url: str, target_domain: str) -> bool:
    if not url:
        return False
    # Exclude known tracking/ad redirect domains
    if any(domain in url for domain in ["bing.com", "duckduckgo.com", "doubleclick.net", "googleadservices.com"]):
        return False
    try:
        parsed = urlparse(url)
        return parsed.netloc and target_domain in parsed.netloc
    except Exception:
        return False


_ddg_breaker = CircuitBreaker(name="duckduckgo", threshold=3, reset_timeout=60)
_google_breaker = CircuitBreaker(name="google_patents", threshold=3, reset_timeout=60)


# ── Concrete scraper classes ──────────────────────────────────────────


class GooglePatentsScraper(BaseScraper):
    """Scrape Google Patents via DDG discovery + HTML parsing."""

    def __init__(self):
        super().__init__(source_name="google_patents")
        self._breaker = _google_breaker

    async def fetch(self, patent_id: str) -> PatentRecord | None:
        url = f"https://patents.google.com/patent/{patent_id}/en/"
        html = await self.fetch_html(url)
        if not html:
            return None
        parsed = parse_google_patent_html(html)
        if not parsed:
            return None
        return _parsed_to_record(parsed)

    async def search(self, query: str) -> List[PatentRecord]:
        """Search via DDG discovery, fetch and parse result pages."""
        query = sanitize_query(query)
        try:
            results = await _ddg_search(f"site:patents.google.com {query}", max_results=5)
        except CircuitOpenError:
            logger.warning("DDG circuit breaker OPEN, skipping Google Patents discovery")
            return []
        except Exception:
            return []

        urls = []
        for r in results:
            href = r.get("href", "")
            if is_clean_url(href, "patents.google.com") and "patents.google.com/patent/" in href:
                urls.append(href)

        return await _fetch_patents_from_urls(urls, parse_google_patent_html, breaker=self._breaker)


class WIPOScraper(BaseScraper):
    """Scrape WIPO PATENTSCOPE via DDG discovery + HTML parsing."""

    def __init__(self):
        super().__init__(source_name="wipo")

    async def fetch(self, patent_id: str) -> PatentRecord | None:
        url = f"https://patentscope.wipo.int/search/en/detail.jsf?docId={patent_id}"
        html = await self.fetch_html(url)
        if not html:
            return None
        parsed = parse_wipo_patent_html(html)
        if not parsed:
            return None
        return _parsed_to_record(parsed)

    async def search(self, query: str) -> List[PatentRecord]:
        """Search via DDG discovery, fall back to snippet data."""
        query = sanitize_query(query)
        try:
            results = await _ddg_search(f"site:patentscope.wipo.int {query}", max_results=5)
        except CircuitOpenError:
            logger.warning("DDG circuit breaker OPEN, skipping WIPO discovery")
            return []
        except Exception:
            return []

        records: list[PatentRecord] = []
        seen_ids: set[str] = set()

        patent_urls = []
        for r in results:
            href = r.get("href", "")
            if not is_clean_url(href, "patentscope.wipo.int"):
                continue
            title_lower = (r.get("title") or "").lower()
            if any(kw in title_lower for kw in ["passkey", "sign in", "log in", "register", "create account"]):
                continue
            patent_urls.append(href)

        if patent_urls:
            page_records = await _fetch_patents_from_urls(
                patent_urls, parse_wipo_patent_html, timeout=6.0
            )
            if page_records:
                return page_records

        for r in results:
            href = r.get("href", "")
            if not is_clean_url(href, "patentscope.wipo.int"):
                continue

            title_lower = (r.get("title") or "").lower()
            if any(kw in title_lower for kw in ["passkey", "sign in", "log in", "register", "create account"]):
                continue

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

            title = title_raw.strip() if title_raw else "[?]"
            for prefix in [pid, pid.replace("WO", "WO/"), pid.replace("WO", "Wo/")]:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip().lstrip("- ")
            if not title:
                title = "[?]"

            abstract = snippet.strip() if snippet else "[?]"

            parsed_assignee = "[?]"
            parsed_dates: dict[str, str] = {"filed": "[?]"}
            try:
                html = await self.fetch_html(href, timeout=6.0)
                if html:
                    parsed = parse_wipo_patent_html(html)
                    if parsed:
                        if parsed.get("assignee") and parsed["assignee"] != "[?]":
                            parsed_assignee = parsed["assignee"]
                        if parsed.get("dates"):
                            parsed_dates = parsed["dates"]
            except Exception:
                pass

            records.append(PatentRecord(
                id=pid,
                title=title,
                assignee=parsed_assignee,
                dates=parsed_dates,
                abstract=abstract,
                claims=["[?]"],
                image_urls=["[?]"],
                status="UNKNOWN",
                family_id="UNKNOWN",
            ))

        return records


class LensScraper(BaseScraper):
    """Scrape Lens.org via DDG snippet data (JS-rendered pages)."""

    def __init__(self):
        super().__init__(source_name="lens")

    async def fetch(self, patent_id: str) -> PatentRecord | None:
        return None

    async def search(self, query: str) -> List[PatentRecord]:
        query = sanitize_query(query)
        try:
            results = await _ddg_search(f"site:lens.org/lens/patent {query}", max_results=5)
        except CircuitOpenError:
            logger.warning("DDG circuit breaker OPEN, skipping Lens discovery")
            return []
        except Exception:
            return []

        records: list[PatentRecord] = []
        seen_ids: set[str] = set()
        _PATENT_NUM_RE = re.compile(r"[A-Z]{2}\d{4,}[A-Z0-9]{0,3}")

        for r in results:
            href = r.get("href", "")
            if not is_clean_url(href, "lens.org"):
                continue
            if "lens.org/lens/patent/" not in href:
                continue

            title_raw = r.get("title", "")
            snippet = r.get("body", "")

            pid = None
            m = re.search(r"/lens/patent/([\w-]+)", href)
            if m:
                pid = m.group(1)

            if not pid or pid in seen_ids:
                continue

            actual_pn = None
            for text in [title_raw, snippet]:
                if text:
                    m2 = _PATENT_NUM_RE.search(text)
                    if m2:
                        actual_pn = re.sub(r'\s+', '', m2.group(0))
                        break
            final_id = actual_pn if actual_pn else pid
            seen_ids.add(final_id)

            filed = "[?]"
            if snippet:
                dm = re.search(r"(\d{4}-\d{2}-\d{2})", snippet)
                if dm:
                    filed = dm.group(1)

            assignee = "[?]"
            title_clean = title_raw.strip() if title_raw else "[?]"
            for sep in [" — ", " - ", " – "]:
                parts = title_clean.split(sep, 1)
                if len(parts) == 2:
                    potential_assignee = parts[1].strip()
                    if potential_assignee and not _PATENT_NUM_RE.fullmatch(potential_assignee):
                        assignee = potential_assignee
                        title_clean = parts[0].strip()
                        break

            abstract = snippet.strip() if snippet else "[?]"

            records.append(PatentRecord(
                id=final_id,
                title=title_clean,
                assignee=assignee,
                dates={"filed": filed},
                abstract=abstract,
                claims=["[?]"],
                image_urls=["[?]"],
                status="UNKNOWN",
                family_id="UNKNOWN",
            ))

        return records


class EPOScraper(BaseScraper):
    """Scrape EPO Register via DDG discovery + HTML deep-fetch."""

    def __init__(self):
        super().__init__(source_name="epo")

    async def fetch(self, patent_id: str) -> PatentRecord | None:
        ep_num = patent_id[2:] if patent_id.startswith("EP") else patent_id
        url = f"https://register.epo.org/application?number=EP{ep_num}"
        html = await self.fetch_html(url)
        if not html:
            return None
        return _parse_epo_detail_to_record(html, patent_id)

    async def search(self, query: str) -> List[PatentRecord]:
        query = sanitize_query(query)
        try:
            results = await _ddg_search(f"site:register.epo.org {query}", max_results=5)
        except CircuitOpenError:
            logger.warning("DDG circuit breaker OPEN, skipping EPO discovery")
            return []
        except Exception:
            return []

        records: list[PatentRecord] = []
        seen_ids: set[str] = set()

        for r in results:
            href = r.get("href", "")
            if not is_clean_url(href, "register.epo.org"):
                continue

            title_raw = r.get("title", "")
            snippet = r.get("body", "")

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

        if records:
            for rec in records:
                try:
                    ep_num = rec.id[2:] if rec.id.startswith("EP") else rec.id
                    ep_url = f"https://register.epo.org/application?number=EP{ep_num}"
                    html = await self.fetch_html(ep_url, timeout=8.0)
                    if not html:
                        continue
                    enriched = _parse_epo_detail_to_record(html, rec.id)
                    if enriched:
                        if enriched.title != "[?]":
                            rec.title = enriched.title
                        if enriched.assignee != "[?]":
                            rec.assignee = enriched.assignee
                        if enriched.abstract != "[?]":
                            rec.abstract = enriched.abstract
                        if enriched.dates.get("filed", "[?]") != "[?]":
                            rec.dates["filed"] = enriched.dates["filed"]
                except Exception:
                    continue

        return records


# ── Parsing helpers (module-level for testability) ────────────────────


def parse_google_patent_html(html: str) -> dict | None:
    """Parse a single Google Patents page and extract patent fields."""
    soup = BeautifulSoup(html, "lxml")

    pn_el = soup.select_one("[itemprop='publicationNumber'], [data-patent-number]")
    pn = pn_el.get_text(separator=" ", strip=True) if pn_el else None

    if not pn:
        title_tag = soup.find("title")
        if title_tag:
            m = re.search(r"([A-Z]{2}\d+[A-Z0-9]*)", title_tag.get_text())
            if m:
                pn = m.group(1)

    title_el = soup.select_one("[itemprop='title'], h1, .patent-title")
    title = title_el.get_text(separator=" ", strip=True) if title_el else "[?]"

    assignee_el = soup.select_one("[itemprop='assignee'], .assignee, .patent-assignee")
    assignee = assignee_el.get_text(separator=" ", strip=True) if assignee_el else "[?]"

    abstract_el = soup.select_one("[itemprop='abstract'], .abstract, .patent-abstract")
    abstract = abstract_el.get_text(separator=" ", strip=True) if abstract_el else "[?]"

    date_el = soup.select_one("[itemprop='filingDate'], [itemprop='datePublished'], .filing-date, .pub-date")
    filed = date_el.get("content") or date_el.get_text(separator=" ", strip=True) if date_el else "[?]"
    if filed and filed != "[?]":
        filed = filed[:10]

    status_el = soup.select_one("[itemprop='status'], .status, .legal-status")
    status = status_el.get_text(separator=" ", strip=True) if status_el else "UNKNOWN"

    claims: list[str] = []
    claim_els = soup.select("[itemprop='claims'], .patent-claims")
    for ce in claim_els:
        text = ce.get_text(separator=" ", strip=True)
        if text:
            claims.append(text)
        if len(claims) >= 10:
            break
    if not claims:
        claims = []

    image_urls: list[str] = []
    img_uri_el = soup.select_one("[itemprop='representativePublicationFigureUri']")
    if img_uri_el:
        src = img_uri_el.get("src") or img_uri_el.get("href") or img_uri_el.get_text(separator=" ", strip=True)
        if src:
            image_urls.append(src)
    if not image_urls:
        for img in soup.select("img.patent-image"):
            src = img.get("src")
            if src:
                image_urls.append(src)

    return {
        "id": pn or "UNKNOWN",
        "title": title,
        "assignee": assignee,
        "abstract": abstract,
        "dates": {"filed": filed} if filed != "[?]" else {},
        "status": status[:20],
        "claims": claims,
        "image_urls": image_urls,
    }


def parse_wipo_patent_html(html: str) -> dict | None:
    """Parse a single WIPO PATENTSCOPE page."""
    soup = BeautifulSoup(html, "lxml")

    pn_el = soup.select_one(".patent-number, .publication-number, [id*='pubNumber']")
    pn = pn_el.get_text(separator=" ", strip=True) if pn_el else None

    if not pn:
        m = re.search(r"(WO\d{4}\d+)", html)
        if m:
            pn = m.group(1)

    title_el = soup.select_one(".title, .invention-title, h1")
    title = title_el.get_text(separator=" ", strip=True) if title_el else "[?]"

    assignee_el = soup.select_one(".applicant, .assignee, [id*='applicant']")
    assignee = assignee_el.get_text(separator=" ", strip=True) if assignee_el else "[?]"

    abstract_el = soup.select_one(".abstract, [id*='abstract']")
    abstract = abstract_el.get_text(separator=" ", strip=True) if abstract_el else "[?]"

    filed = "[?]"
    pub_date_el = soup.select_one(
        "meta[name='pubDate'], meta[name='filingDate'], "
        "[itemprop='filingDate'], [itemprop='datePublished'], "
        ".publication-date, .filing-date, .date"
    )
    if pub_date_el:
        d = pub_date_el.get("content") or pub_date_el.get_text(separator=" ", strip=True)
        if d:
            d = d[:10]
            if re.match(r"\d{4}-\d{2}-\d{2}", d):
                filed = d

    if filed == "[?]":
        for tag in soup.find_all(["span", "td", "div"]):
            text = tag.get_text(separator=" ", strip=True)
            m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            if m:
                filed = m.group(1)
                break

    return {
        "id": pn or "UNKNOWN",
        "title": title,
        "assignee": assignee,
        "abstract": abstract,
        "dates": {"filed": filed} if filed != "[?]" else {},
        "status": "UNKNOWN",
    }


def _parse_epo_detail_to_record(html: str, patent_id: str) -> PatentRecord | None:
    """Parse EPO register HTML into a PatentRecord."""
    soup = BeautifulSoup(html, "lxml")

    title = "[?]"
    title_el = soup.select_one("h1, .page-title")
    if title_el:
        t = title_el.get_text(separator=" ", strip=True)
        if t:
            title = t

    assignee = "[?]"
    applicant_el = soup.select_one(".applicant, [id*='applicant']")
    if not applicant_el:
        for td in soup.find_all("td"):
            if "applicant" in td.get_text(separator=" ", strip=True).lower():
                sibling = td.find_next("td")
                if sibling:
                    applicant_el = sibling
                break
    if applicant_el:
        a_text = applicant_el.get_text(separator=" ", strip=True)
        a_text = re.sub(r"(?i)for all designated states\s*", "", a_text)
        parts = re.split(r",|\d", a_text)
        clean_assignee = parts[0].strip()
        if clean_assignee:
            assignee = clean_assignee

    abstract = "[?]"
    abstract_el = soup.select_one(".abstract, [id*='abstract'], .patent-abstract")
    if abstract_el:
        ab = abstract_el.get_text(separator=" ", strip=True)
        if ab:
            abstract = ab

    filed = "[?]"
    date_texts = soup.get_text()
    dm = re.search(r"(\d{4}-\d{2}-\d{2})", date_texts)
    if not dm:
        dm = re.search(r"(\d{2}\.\d{2}\.\d{4})", date_texts)
    if dm:
        filed = dm.group(1)[:10]

    return PatentRecord(
        id=patent_id,
        title=title,
        assignee=assignee,
        dates={"filed": filed} if filed != "[?]" else {},
        abstract=abstract,
        claims=["[?]"],
        image_urls=["[?]"],
        status="UNKNOWN",
        family_id="UNKNOWN",
    )


# ── Shared helpers ────────────────────────────────────────────────────


async def _ddg_search(query: str, max_results: int = 5) -> list:
    """Search DuckDuckGo via ddgs library, capped at 2 concurrent workers."""
    _ddg_breaker.check()
    async with _DDG_SEMAPHORE:
        await asyncio.sleep(random.uniform(1.0, 3.0))
        from ddgs import DDGS
        def _sync_search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        try:
            return await asyncio.wait_for(asyncio.to_thread(_sync_search), timeout=8.0)
        except asyncio.TimeoutError:
            _ddg_breaker.record_failure()
            return []


async def _fetch_patents_from_urls(
    urls: list[str], parser_fn, timeout: float = 8.0, breaker: CircuitBreaker | None = None
) -> list[PatentRecord]:
    """Fetch patent pages concurrently and parse them."""
    scraper = GooglePatentsScraper()
    seen_ids: set[str] = set()
    records: list[PatentRecord] = []

    async def _fetch_and_parse(url: str) -> PatentRecord | None:
        html = await scraper.fetch_html(url, timeout=timeout)
        if not html:
            return None
        if breaker:
            breaker.check()
        parsed = await asyncio.to_thread(parser_fn, html)
        if not parsed:
            return None
        if breaker:
            breaker.record_success()

        pid = parsed["id"]
        if pid in seen_ids:
            return None
        seen_ids.add(pid)

        return _parsed_to_record(parsed)

    tasks = [_fetch_and_parse(u) for u in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, PatentRecord):
            records.append(r)
    return records


def _parsed_to_record(parsed: dict) -> PatentRecord:
    """Convert parsed dict to PatentRecord."""
    if not parsed.get("dates"):
        parsed["dates"] = {"filed": "[?]"}
    if not parsed.get("status"):
        parsed["status"] = "UNKNOWN"
    return PatentRecord(
        id=parsed["id"],
        title=parsed["title"],
        assignee=parsed["assignee"],
        dates=parsed["dates"],
        abstract=parsed["abstract"],
        claims=parsed.get("claims", []),
        image_urls=parsed.get("image_urls", []),
        status=parsed["status"],
        family_id="UNKNOWN",
    )


# ── Public API (unchanged signatures) ─────────────────────────────────


async def search_google_patents(query: str) -> List[PatentRecord]:
    """Search Google Patents via DuckDuckGo discovery + HTML scraping."""
    return await GooglePatentsScraper().search(query)


async def search_wipo_patents(query: str) -> List[PatentRecord]:
    """Search WIPO PATENTSCOPE via DuckDuckGo snippet data."""
    return await WIPOScraper().search(query)


async def search_lens_patents(query: str) -> List[PatentRecord]:
    """Search Lens.org via DuckDuckGo snippet data."""
    return await LensScraper().search(query)


async def search_epo_patents(query: str) -> List[PatentRecord]:
    """Search EPO Register via DuckDuckGo snippet data."""
    return await EPOScraper().search(query)
