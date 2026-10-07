"""Tests for dates completion: GP page parsing (expires/family/status)
and the deterministic expiration estimator."""

from clients.scrapers import parse_google_patent_html
from core.models import estimate_expiration

_GP_HTML = """<html><head><title>US11942620B2 - Bipolar solid-state battery
- Google Patents</title></head><body>
<span itemprop="publicationNumber">US11942620B2</span>
<h1 itemprop="title">Bipolar solid-state battery</h1>
<span itemprop="assignee">Toyota</span>
<span itemprop="abstract">A bipolar battery.</span>
<time itemprop="filingDate" datetime="2021-12-06">2021-12-06</time>
<span itemprop="legalStatus">Active</span>
<span itemprop="expiration" datetime="2041-12-09">2041-12-09</span>
<table><tbody>
<tr itemprop="docdbFamily"><td><a href="/patent/US20220181598A1/en">A</a></td></tr>
<tr itemprop="docdbFamily"><td><a href="/patent/CN114597486A/en">B</a></td></tr>
</tbody></table>
</body></html>"""


class TestParseGooglePatentDates:
    def test_parses_legal_status(self):
        parsed = parse_google_patent_html(_GP_HTML)
        assert parsed["status"] == "Active"

    def test_parses_expiration(self):
        parsed = parse_google_patent_html(_GP_HTML)
        assert parsed["dates"]["expires"] == "2041-12-09"

    def test_family_counts_rows_plus_self(self):
        parsed = parse_google_patent_html(_GP_HTML)
        assert parsed["dates"]["family_count"] == "3"  # 2 rows + this patent

    def test_no_family_markup_leaves_fields_absent(self):
        html = _GP_HTML.replace("docdbFamily", "nothing").replace(
            'itemprop="expiration" datetime="2041-12-09"', 'data-x="1"'
        )
        parsed = parse_google_patent_html(html)
        assert "family_count" not in parsed["dates"]
        assert "expires" not in parsed["dates"]

    def test_status_falls_back_without_legal_status(self):
        html = _GP_HTML.replace('itemprop="legalStatus"', 'itemprop="nope"')
        parsed = parse_google_patent_html(html)
        assert parsed["status"] == "UNKNOWN"


class TestEstimateExpiration:
    def test_explicit_expiration_wins(self):
        dates = {"filed": "2021-12-06", "expires": "2041-12-09"}
        assert estimate_expiration(dates, "US11942620B2") == "2041-12-09"

    def test_computed_twenty_years_from_filing(self):
        assert estimate_expiration({"filed": "2021-12-06"}, "US11942620B2") == (
            "2041-12-06 (est.)"
        )

    def test_design_patent_not_estimated(self):
        assert estimate_expiration({"filed": "2021-12-06"}, "USD0999123S") == "[?]"

    def test_missing_filing_date(self):
        assert estimate_expiration({}, "US11942620B2") == "[?]"
        assert estimate_expiration({"filed": "[?]"}, "US11942620B2") == "[?]"

    def test_invalid_filing_date(self):
        assert estimate_expiration({"filed": "not-a-date"}, "US11942620B2") == "[?]"

    def test_feb29_filing_still_estimates(self):
        result = estimate_expiration({"filed": "2000-02-29"}, "US11942620B2")
        assert result.startswith("20")
        assert result.endswith("(est.)")

    def test_placeholder_expiration_ignored(self):
        assert estimate_expiration({"filed": "2021-12-06", "expires": "[?]"}) == (
            "2041-12-06 (est.)"
        )
