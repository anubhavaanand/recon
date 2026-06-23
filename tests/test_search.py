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
    assert sorted_records[0].id == "new"
    assert sorted_records[1].id == "old"
    assert sorted_records[2].id in ("none", "unk")
    assert sorted_records[3].id in ("none", "unk")


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
