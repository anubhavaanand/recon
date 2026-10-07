"""Tests for Boolean query mode (core.query) — field operators, phrases, AND."""

from core.models import PatentRecord
from core.query import (
    apply_boolean_filter,
    matches_boolean,
    parse_boolean_query,
    to_keyword_query,
)
from core.search import sanitize_query


def _record(title="Solid state battery", abstract="Sulfide electrolyte layer",
            assignee="Toyota Motor Corp", **kw):
    return PatentRecord(
        id=kw.pop("id", "US11942620B2"),
        title=title,
        assignee=assignee,
        dates=kw.pop("dates", {"filed": "2021-12-06"}),
        abstract=abstract,
        claims=kw.pop("claims", []),
        image_urls=kw.pop("image_urls", []),
        status=kw.pop("status", "UNKNOWN"),
        family_id=kw.pop("family_id", "UNKNOWN"),
    )


class TestParse:
    def test_field_prefix_detected(self):
        bq = parse_boolean_query("ti:battery")
        assert bq.is_boolean
        assert bq.constraints == [("title", "battery")]

    def test_quoted_phrase(self):
        bq = parse_boolean_query('ti:"solid state" ab:electrolyte')
        assert ("title", "solid state") in bq.constraints
        assert ("abstract", "electrolyte") in bq.constraints

    def test_assignee_and_alias(self):
        assert parse_boolean_query("assignee:Toyota").constraints == [("assignee", "Toyota")]
        assert parse_boolean_query("an:Toyota").constraints == [("assignee", "Toyota")]

    def test_plain_query_is_not_boolean(self):
        bq = parse_boolean_query("solid state battery")
        assert not bq.is_boolean
        assert bq.terms == ["solid", "state", "battery"]

    def test_unknown_prefix_becomes_free_text(self):
        bq = parse_boolean_query("foo:bar ti:battery")
        assert bq.constraints == [("title", "battery")]
        assert bq.terms == ["foo:bar"]

    def test_survives_sanitization(self):
        clean = sanitize_query('ti:"solid state" ab:electrolyte')
        bq = parse_boolean_query(clean)
        assert bq.is_boolean
        assert ("title", "solid state") in bq.constraints


class TestToKeywordQuery:
    def test_strips_prefixes_keeps_terms(self):
        bq = parse_boolean_query('ti:"solid state" ab:electrolyte lithium')
        assert to_keyword_query(bq) == "solid state electrolyte lithium"


class TestMatches:
    def test_title_constraint(self):
        bq = parse_boolean_query("ti:battery")
        assert matches_boolean(_record(), bq)

    def test_title_constraint_rejects(self):
        bq = parse_boolean_query("ti:semiconductor")
        assert not matches_boolean(_record(), bq)

    def test_abstract_missing_placeholder(self):
        bq = parse_boolean_query("ab:electrolyte")
        assert matches_boolean(_record(), bq)
        assert not matches_boolean(_record(abstract="[?]"), bq)

    def test_assignee_constraint(self):
        bq = parse_boolean_query("assignee:toyota")
        assert matches_boolean(_record(), bq)
        assert not matches_boolean(_record(assignee="[?]"), bq)

    def test_and_semantics(self):
        bq = parse_boolean_query("ti:battery ab:electrolyte")
        assert matches_boolean(_record(), bq)
        assert not matches_boolean(_record(abstract="ceramic housing"), bq)

    def test_free_text_matches_title_or_abstract(self):
        bq = parse_boolean_query("ti:battery sulfide")
        assert matches_boolean(_record(), bq)
        assert not matches_boolean(_record(abstract="cathode coating"), bq)


class TestApplyFilter:
    def test_passthrough_without_operators(self):
        records = [_record(), _record(title="Other")]
        assert apply_boolean_filter(records, "solid state battery") is records

    def test_narrows_preserving_order(self):
        records = [
            _record(id="US1"),
            _record(id="EP2", title="Semiconductor package"),
            _record(id="WO3", title="Battery pack for vehicles"),
        ]
        out = apply_boolean_filter(records, "ti:battery")
        assert [r.id for r in out] == ["US1", "WO3"]

    def test_empty_constraint_result(self):
        out = apply_boolean_filter([_record()], "ti:quantum")
        assert out == []
