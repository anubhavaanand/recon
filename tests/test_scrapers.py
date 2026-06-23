"""Tests for clients/scrapers.py - Phase 1 scraper deep-fetch changes.

Tests cover:
  - _parse_google_patent_html: claims and image URL extraction
  - _parse_wipo_patent_html: date extraction from meta/fallback
  - search_lens_patents: assignee and patent number extraction
  - search_epo_patents: deep-fetch graceful failure and enrichment
"""

import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch

from clients.scrapers import (
    _parse_google_patent_html,
    _parse_wipo_patent_html,
    search_lens_patents,
    search_epo_patents,
)


# =============================================================================
# Google Patents Claims / Images
# =============================================================================

def test_parse_google_patent_claims():
    """Verify claims are extracted from [itemprop='claims'] divs (max 10)."""
    claim_texts = [f"Claim {i}: A solid state battery with feature {i}." for i in range(12)]
    claims_html = "".join(f'<div itemprop="claims">{t}</div>' for t in claim_texts)

    html = f"""<html><head><title>US12046712B2 - Battery</title></head>
<body>
<div itemprop='publicationNumber'>US12046712B2</div>
<div itemprop='title'>Solid State Battery</div>
<div itemprop='assignee'>ACME Corp</div>
<div itemprop='abstract'>A solid state battery.</div>
<div itemprop='filingDate' content='2022-06-15'></div>
<div itemprop='status'>Active</div>
{claims_html}
</body></html>"""

    result = _parse_google_patent_html(html)
    assert result is not None
    assert "claims" in result
    assert len(result["claims"]) == 10
    # First 10 claims should be present
    for i in range(10):
        assert f"Claim {i}:" in result["claims"][i]
    # The 12th claim should NOT be included (capped at 10)
    assert "Claim 11:" not in result["claims"]


def test_parse_google_patent_images():
    """Verify image_urls from itemprop and img.patent-image fallback."""
    html = """<html><head><title>US12046712B2</title></head>
<body>
<div itemprop='publicationNumber'>US12046712B2</div>
<div itemprop='title'>Solid State Battery</div>
<div itemprop='assignee'>ACME Corp</div>
<div itemprop='abstract'>A solid state battery.</div>
<div itemprop='filingDate' content='2022-06-15'></div>
<div itemprop='status'>Active</div>
<link itemprop='representativePublicationFigureUri' href='https://example.com/fig1.svg' />
<img class='patent-image' src='https://example.com/fig2.png' />
</body></html>"""

    result = _parse_google_patent_html(html)
    assert result is not None
    assert "image_urls" in result
    # The itemprop path takes priority; img fallback not triggered
    assert len(result["image_urls"]) >= 1
    assert "https://example.com/fig1.svg" in result["image_urls"]


def test_parse_google_patent_images_fallback():
    """Verify image_urls fallback to img.patent-image when no itemprop."""
    html = """<html><head><title>US12046712B2</title></head>
<body>
<div itemprop='publicationNumber'>US12046712B2</div>
<div itemprop='title'>Solid State Battery</div>
<div itemprop='assignee'>ACME Corp</div>
<div itemprop='abstract'>A solid state battery.</div>
<div itemprop='filingDate' content='2022-06-15'></div>
<div itemprop='status'>Active</div>
<img class='patent-image' src='https://example.com/fig1.png' />
<img class='patent-image' src='https://example.com/fig2.png' />
</body></html>"""

    result = _parse_google_patent_html(html)
    assert result is not None
    assert "image_urls" in result
    assert len(result["image_urls"]) >= 2
    assert "https://example.com/fig1.png" in result["image_urls"]
    assert "https://example.com/fig2.png" in result["image_urls"]


# =============================================================================
# WIPO Dates
# =============================================================================

def test_parse_wipo_patent_dates_meta():
    """Verify filing date extracted from meta[name='pubDate'] content."""
    html = """<html><head>
<meta name='pubDate' content='2020-01-15' />
</head>
<body>
<div class='patent-number'>WO2020123456</div>
<div class='title'>Battery Technology</div>
<div class='applicant'>WIPO Corp</div>
<div class='abstract'>A battery technology.</div>
</body></html>"""

    result = _parse_wipo_patent_html(html)
    assert result is not None
    assert "dates" in result
    assert result["dates"].get("filed") == "2020-01-15"


def test_parse_wipo_patent_dates_fallback():
    """Verify fallback date extraction from date-like text in page."""
    html = """<html><head></head>
<body>
<div class='patent-number'>WO2020123456</div>
<div class='title'>Battery Technology</div>
<div class='applicant'>WIPO Corp</div>
<div class='abstract'>A battery technology.</div>
<span>Published: 2020-06-15</span>
</body></html>"""

    result = _parse_wipo_patent_html(html)
    assert result is not None
    assert "dates" in result
    assert result["dates"].get("filed") == "2020-06-15"


# =============================================================================
# Lens Snippet
# =============================================================================

_LENS_BASE = {
    "href": "https://lens.org/lens/patent/123-456-789-000-xxx",
    "title": "Lithium Battery - Tesla Inc",
    "body": "A lithium battery with high energy density. 2023-06-15.",
}


@pytest.mark.asyncio
async def test_lens_snippet_assignee_extraction():
    """Verify assignee parsed from title after ' - ' separator."""
    with patch("ddgs.DDGS") as mock_ddgs:
        mock_ddgs.return_value.__enter__.return_value.text.return_value = [
            _LENS_BASE,
        ]
        records = await search_lens_patents("battery")

    assert len(records) == 1
    rec = records[0]
    assert rec.assignee == "Tesla Inc"
    assert rec.title == "Lithium Battery"


@pytest.mark.asyncio
async def test_lens_snippet_patent_number_replacement():
    """Verify Lens internal ID replaced by actual patent number from snippet."""
    result = dict(_LENS_BASE)
    result["body"] = "US12345678B2 shows a lithium battery. 2023-06-15."

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_ddgs.return_value.__enter__.return_value.text.return_value = [
            result,
        ]
        records = await search_lens_patents("battery")

    assert len(records) == 1
    rec = records[0]
    assert rec.id == "US12345678B2"  # actual patent number, not Lens internal ID
    assert rec.assignee == "Tesla Inc"


@pytest.mark.asyncio
async def test_lens_snippet_date_extraction():
    """Verify date parsed from snippet with regex \\d{4}-\\d{2}-\\d{2}."""
    with patch("ddgs.DDGS") as mock_ddgs:
        mock_ddgs.return_value.__enter__.return_value.text.return_value = [
            _LENS_BASE,
        ]
        records = await search_lens_patents("battery")

    assert len(records) == 1
    assert records[0].dates.get("filed") == "2023-06-15"


# =============================================================================
# EPO Deep-Fetch
# =============================================================================

_EPO_BASE = {
    "href": "https://register.epo.org/application?number=EP12345678",
    "title": "EP12345678 - Solid State Battery",
    "body": "A solid state battery with improved electrolyte stability.",
}

_EPO_ENRICH_HTML = """<html><body>
<h1>Enriched Title: Solid State Battery</h1>
<div class="applicant">EPO Applicant GmbH</div>
<div class="abstract">Enriched abstract for solid state battery.</div>
<div>Filing date: 2023-01-15</div>
</body></html>"""


@pytest.mark.asyncio
async def test_epo_deep_fetch_graceful_failure(monkeypatch):
    """When _fetch_html returns None (Cloudflare block), snippet data preserved."""
    async def _mock_fetch_html_none(url, timeout=15.0):
        return None

    monkeypatch.setattr("clients.scrapers._fetch_html", _mock_fetch_html_none)

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_ddgs.return_value.__enter__.return_value.text.return_value = [
            _EPO_BASE,
        ]
        records = await search_epo_patents("battery")

    assert len(records) == 1
    rec = records[0]
    assert rec.id == "EP12345678"
    assert rec.title == "EP12345678 - Solid State Battery"  # from snippet
    assert rec.assignee == "[?]"  # not enriched
    assert rec.dates.get("filed") == "[?]"  # not enriched
    assert "improved electrolyte" in rec.abstract  # from snippet


@pytest.mark.asyncio
async def test_epo_deep_fetch_enriches_record(monkeypatch):
    """When _fetch_html returns HTML, record fields updated."""
    async def _mock_fetch_html_enrich(url, timeout=15.0):
        return _EPO_ENRICH_HTML

    monkeypatch.setattr("clients.scrapers._fetch_html", _mock_fetch_html_enrich)

    with patch("ddgs.DDGS") as mock_ddgs:
        mock_ddgs.return_value.__enter__.return_value.text.return_value = [
            _EPO_BASE,
        ]
        records = await search_epo_patents("battery")

    assert len(records) == 1
    rec = records[0]
    assert rec.id == "EP12345678"
    assert rec.title == "Enriched Title: Solid State Battery"  # from deep-fetch h1
    assert rec.assignee == "EPO Applicant GmbH"  # from deep-fetch
    assert "Enriched abstract" in rec.abstract  # from deep-fetch
    assert rec.dates.get("filed") == "2023-01-15"  # from deep-fetch date text
