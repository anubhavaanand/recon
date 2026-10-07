"""Boolean query mode — the "Mode: [Boolean ▼]" from the original Phase-2 sketch.

Field operators scope a term to a record field; bare terms match title or
abstract. Constraints combine with implicit AND. Quoted phrases are kept
whole. Unknown ``foo:`` prefixes are treated as free text, never dropped
(constitution: uncertainty flagged, entries never silently lost).

Deterministic and AI-free: parsing and matching are pure functions, so the
same query always yields the same filter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_FIELDS = {
    "ti": "title",
    "ab": "abstract",
    "assignee": "assignee",
    "an": "assignee",  # assignee name — common patent-search alias
}

_TOKEN_RE = re.compile(r'([a-zA-Z]+):(?:"([^"]*)"|(\S+))|("([^"]*)")|(\S+)')


@dataclass
class BooleanQuery:
    """Parsed boolean query: field-scoped constraints + free-text terms."""

    constraints: list[tuple[str, str]] = field(default_factory=list)
    terms: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def is_boolean(self) -> bool:
        return bool(self.constraints)

    def describe(self) -> str:
        parts = [f"{fld}:{term}" for fld, term in self.constraints]
        parts.extend(self.terms)
        return " AND ".join(parts) if parts else self.raw


def parse_boolean_query(query: str) -> BooleanQuery:
    """Parse a query into field constraints and free-text terms."""
    bq = BooleanQuery(raw=query)
    for match in _TOKEN_RE.finditer(query):
        field_prefix, quoted_field, bare_field, quoted_term, _, bare = match.groups()
        if field_prefix:
            mapped = _FIELDS.get(field_prefix.lower())
            value = quoted_field if quoted_field is not None else bare_field
            if mapped and value:
                bq.constraints.append((mapped, value))
            elif value:
                # Unknown prefix (e.g. an email address) — free text, never dropped.
                bq.terms.append(f"{field_prefix}:{value}")
        elif quoted_term:
            bq.terms.append(quoted_term)
        elif bare:
            bq.terms.append(bare)
    return bq


def to_keyword_query(bq: BooleanQuery) -> str:
    """Reduce to a plain keyword string safe to send to any API."""
    parts = [term for _, term in bq.constraints] + list(bq.terms)
    return " ".join(parts).strip()


def _contains(haystack: str, needle: str) -> bool:
    return needle.lower() in (haystack or "").lower()


def matches_boolean(record, bq: BooleanQuery) -> bool:
    """True when the record satisfies every constraint and free-text term."""
    title = record.title if record.title not in ("[?]", "", None) else ""
    abstract = record.abstract if record.abstract not in ("[?]", "", None) else ""
    assignee = record.assignee if record.assignee not in ("[?]", "", None) else ""
    searchable = f"{title} {abstract}"
    for fld, term in bq.constraints:
        target = {"title": title, "abstract": abstract, "assignee": assignee}[fld]
        if not _contains(target, term):
            return False
    return all(_contains(searchable, term) for term in bq.terms)


def apply_boolean_filter(records: list, query: str) -> list:
    """Filter records when the query uses field operators; otherwise pass through.

    Order is preserved — filtering only narrows, never reorders.
    """
    bq = parse_boolean_query(query)
    if not bq.is_boolean:
        return records
    return [r for r in records if matches_boolean(r, bq)]
