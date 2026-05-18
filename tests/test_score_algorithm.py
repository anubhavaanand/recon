"""
Score algorithm unit tests — PRD §5.5.
37-test minimum coverage (PRD §10).
"""
import pytest
from core.scoring import (
    calculate_signal_score,
    render_score_bar,
    render_signal_dots,
    match_entity,
)
from core.models import CrossReference


def _ref(source: str, conf: float = 100.0) -> CrossReference:
    return CrossReference(
        source=source,
        url=f"https://example.com/{source}",
        metadata={"confidence": conf},
    )


# ── match_entity ─────────────────────────────────────────
def test_match_entity_exact():
    assert match_entity("Tesla Inc", "Tesla Inc") == 100.0

def test_match_entity_case_insensitive():
    assert match_entity("tesla inc", "TESLA INC") == 100.0

def test_match_entity_fuzzy():
    score = match_entity("Tesla Incorporated", "Tesla Inc")
    assert score > 50.0


# ── calculate_signal_score ───────────────────────────────
def test_score_no_refs():
    assert calculate_signal_score([]) == 0

def test_score_single_grant():
    assert calculate_signal_score([_ref("NIH")]) == 20

def test_score_grant_plus_corp():
    refs = [_ref("NIH"), _ref("SEC")]
    assert calculate_signal_score(refs) == 40

def test_score_three_signals():
    # NIH (grant) + SEC (corp) + OpenAlex (academic)
    # NIH + OpenAlex also triggers temporal proximity → 4 signals = 80
    refs = [_ref("NIH"), _ref("SEC"), _ref("OpenAlex")]
    score = calculate_signal_score(refs)
    assert score == 80  # grant + corp + academic + temporal (NIH+OA) = 4×20

def test_score_four_signals_with_temporal():
    # grant + academic → temporal proximity detected
    refs = [_ref("NIH"), _ref("SEC"), _ref("OpenAlex"), _ref("Supply Chain")]
    score = calculate_signal_score(refs)
    assert score >= 80  # 4 signals + temporal proximity

def test_score_max_100():
    refs = [_ref("NIH"), _ref("SEC"), _ref("OpenAlex"), _ref("arXiv"), _ref("opencorporates")]
    score = calculate_signal_score(refs)
    assert score <= 100

def test_score_abandoned_penalty():
    # NIH+SEC+OpenAlex = 80 (includes temporal). 80 - 30 = 50
    refs = [_ref("NIH"), _ref("SEC"), _ref("OpenAlex")]
    score = calculate_signal_score(refs, status="ABANDONED")
    assert score == 50

def test_score_shell_company_penalty():
    # NIH+SEC+OpenAlex = 80 (includes temporal). 80 - 20 = 60
    refs = [_ref("NIH"), _ref("SEC"), _ref("OpenAlex")]
    score = calculate_signal_score(refs, shell_company=True)
    assert score == 60

def test_score_combined_penalties_floored_at_zero():
    refs = [_ref("NIH")]  # 20 base
    score = calculate_signal_score(refs, status="ABANDONED", shell_company=True)
    assert score == 0  # 20 - 30 - 20 = -30 → clamped to 0

def test_score_never_exceeds_100():
    refs = [_ref(src) for src in ["NIH", "SEC", "OpenAlex", "arXiv", "opencorporates", "DOE", "NSF"]]
    score = calculate_signal_score(refs)
    assert score == 100


# ── render_score_bar ─────────────────────────────────────
def test_score_bar_zero():
    bar = render_score_bar(0)
    assert bar.startswith("░" * 20) or "0/100" in bar

def test_score_bar_100():
    bar = render_score_bar(100)
    assert "█" * 20 in bar
    assert "100/100" in bar

def test_score_bar_50():
    bar = render_score_bar(50)
    assert "50/100" in bar
    assert "█" * 10 in bar

def test_score_bar_length():
    bar = render_score_bar(75)
    filled = bar.count("█")
    empty  = bar.count("░")
    assert filled + empty == 20


# ── render_signal_dots ───────────────────────────────────
def test_signal_dots_no_refs():
    result = render_signal_dots([])
    assert "No signals" in result

def test_signal_dots_single():
    result = render_signal_dots([_ref("NIH", 100.0)])
    assert "NIH" in result
    assert "●" in result

def test_signal_dots_partial_confidence():
    result = render_signal_dots([_ref("SEC", 60.0)])
    assert "SEC" in result
    # 60% → 3 filled dots
    assert "●●●" in result

def test_signal_dots_multiple_sources():
    refs = [_ref("NIH", 100.0), _ref("SEC", 80.0)]
    result = render_signal_dots(refs)
    assert "NIH" in result
    assert "SEC" in result
