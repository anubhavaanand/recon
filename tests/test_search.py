import pytest
from core.search import sort_and_merge_results
from core.models import PatentRecord


def _make_record(id: str, filed: str) -> PatentRecord:
    return PatentRecord(
        id=id, title="T", assignee="X", dates={"filed": filed},
        abstract="", claims=[], image_urls=[], status="active", family_id="F",
    )


def test_descending_sort_never_drops():
    records = [
        _make_record("1", "2020-01-01"),
        _make_record("2", "2021-01-01"),
        _make_record("3", "2019-01-01"),
    ]
    sorted_records = sort_and_merge_results(records)
    assert len(sorted_records) == 3
    assert sorted_records[0].id == "2"
    assert sorted_records[1].id == "1"
    assert sorted_records[2].id == "3"


def test_missing_dates_sort_last():
    r_old = _make_record("old", "2019-01-01")
    r_new = _make_record("new", "2022-01-01")
    r_none = _make_record("none", "")
    r_unk = _make_record("unk", "[?]")
    sorted_records = sort_and_merge_results([r_none, r_old, r_unk, r_new])
    assert len(sorted_records) == 4
    assert sorted_records[0].id == "NEW"
    assert sorted_records[1].id == "OLD"
    assert sorted_records[2].id in ("NONE", "UNK")
    assert sorted_records[3].id in ("NONE", "UNK")


def test_all_results_present_no_silent_omission():
    records = [_make_record(str(i), f"202{i}-01-01") for i in range(10)]
    sorted_records = sort_and_merge_results(records)
    assert len(sorted_records) == 10
    ids = {r.id for r in sorted_records}
    assert ids == {str(i) for i in range(10)}


def test_descending_sort_order():
    records = [
        _make_record("A", "2022-01-01"),
        _make_record("B", "2022-06-01"),
        _make_record("C", "2021-12-01"),
        _make_record("D", "2023-01-01"),
    ]
    sorted_records = sort_and_merge_results(records)
    dates = [r.dates["filed"] for r in sorted_records]
    assert dates == sorted(dates, reverse=True)


def test_sort_stability():
    records = [
        _make_record("A", "2022-01-01"),
        _make_record("B", "2022-01-01"),
        _make_record("C", "2022-01-01"),
    ]
    sorted_records = sort_and_merge_results(records)
    assert len(sorted_records) == 3


def test_missing_filed_date_default():
    record = _make_record("X", "")
    assert record.dates.get("filed") == "[?]"


def test_missing_dates_flagged_not_imputed():
    r = _make_record("Y", "")
    if not r.dates.get("filed"):
        r.dates["filed"] = "[?]"
    assert r.dates["filed"] == "[?]"


def test_empty_result_set():
    assert sort_and_merge_results([]) == []


def test_single_result():
    r = _make_record("1", "2022-01-01")
    assert sort_and_merge_results([r]) == [r]


@pytest.mark.asyncio
async def test_search_all_returns_list():
    from core.search import search_all
    from unittest.mock import patch
    with patch("core.search.search_all") as mock:
        mock.return_value = [_make_record("1", "2023-01-01")]
        result = await search_all("test")
        assert len(result) > 0


# ── Input sanitization ────────────────────────────────────

def test_sanitize_removes_shell_chars():
    from core.search import sanitize_query
    assert sanitize_query("hello; rm -rf /") == "hello rm -rf /"
    assert sanitize_query("query | whoami") == "query whoami"
    assert sanitize_query("foo & bar") == "foo bar"
    assert sanitize_query("$(dangerous)") == "dangerous"
    assert sanitize_query("`backtick`") == "backtick"


def test_sanitize_removes_cql_injection():
    from core.search import sanitize_query
    assert sanitize_query("*:*") == ""
    assert sanitize_query("query *:*") == "query"


def test_sanitize_preserves_normal_queries():
    from core.search import sanitize_query
    assert sanitize_query("solid state battery") == "solid state battery"
    assert sanitize_query('"quantum computing"') == '"quantum computing"'
    assert sanitize_query("batter*") == "batter*"
    assert sanitize_query("USPTO-123456") == "USPTO-123456"


def test_sanitize_strips_whitespace():
    from core.search import sanitize_query
    assert sanitize_query("  hello world  ") == "hello world"
    assert sanitize_query("") == ""


def test_is_clean_url():
    from clients.scrapers import is_clean_url
    assert is_clean_url("https://patents.google.com/patent/US1000000B1/en", "patents.google.com") is True
    assert is_clean_url("https://patentscope.wipo.int/search/en/detail.jsf", "patentscope.wipo.int") is True
    assert is_clean_url("https://www.bing.com/ck/a?u=https://patents.google.com/patent/US1000000", "patents.google.com") is False
    assert is_clean_url("https://duckduckgo.com/y.js?ad_domain=patents.google.com", "patents.google.com") is False
    assert is_clean_url(None, "lens.org") is False
    assert is_clean_url("", "lens.org") is False


def test_extract_patent_id():
    from clients.scrapers import extract_patent_id
    assert extract_patent_id("US 11,000,000 B2 - battery patent") == "US11000000B2"
    assert extract_patent_id("EP 1 234 567 A1") == "EP1234567A1"
    assert extract_patent_id("WO-2020-123456-A1") == "WO2020123456A1"
    assert extract_patent_id("some random text") is None


@pytest.mark.asyncio
async def test_lens_id_resolution(monkeypatch):
    from clients.scrapers import LensScraper
    class MockResponse:
        status_code = 200
        text = "<html><title>US 11,000,000 B2 - Novel Battery</title></html>"
        
    async def mock_get(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    
    from core.models import PatentRecord
    async def mock_gp_fetch(self, patent_id):
        return PatentRecord(
            id=patent_id,
            title="Resolved Patent",
            assignee="Acme Corp",
            dates={"filed": "2020-01-01"},
            abstract="AB",
            claims=[],
            image_urls=[],
            status="Active",
            family_id="F123"
        )
    monkeypatch.setattr("clients.scrapers.GooglePatentsScraper.fetch", mock_gp_fetch)
    
    scraper = LensScraper()
    record = await scraper.fetch("039-653-535-961-827")
    assert record is not None
    assert record.id == "US11000000B2"
    assert record.title == "Resolved Patent"
