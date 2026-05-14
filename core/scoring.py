"""
PRD §5.4 – Signal Scoring (Constitution §5, Equal Weights)

Five signals, +20 each, max 100. Penalties after sum.
Each signal: +20
  1. Grant funding     (NIH / NSF / DOE)
  2. Corporate filing  (SEC 10-K / 8-K)
  3. Academic citation (OpenAlex / arXiv)
  4. Temporal proximity (filing within 2yr of grant signal)
  5. Supply chain evidence

Penalties:
  ABANDONED status   : -30
  Shell company      : -20 (detected via OpenCorporates signal)
"""

from rapidfuzz import fuzz
from typing import List
from core.models import CrossReference, PatentRecord

# ── Signal source categories ─────────────────────────────
_GRANT_SOURCES   = {"nih", "nsf", "doe", "nih reporter", "nsf awards"}
_CORP_SOURCES    = {"sec", "edgar", "10-k", "8-k"}
_ACADEMIC_SOURCES = {"openalex", "arxiv", "openalexs", "arxiv preprints"}
_SUPPLY_SOURCES  = {"opencorporates", "supply chain", "duns"}


def match_entity(entity1: str, entity2: str) -> float:
    """Returns deterministic similarity score between two entities."""
    if entity1.lower() == entity2.lower():
        return 100.0
    return fuzz.partial_ratio(entity1, entity2)


def calculate_signal_score(
    cross_references: List[CrossReference],
    status: str = "active",
    shell_company: bool = False,
) -> int:
    """
    PRD §5.5 compliant score calculation.
    Returns final score in [0, 100].
    """
    if not cross_references:
        return 0

    # Detect signal types
    sources_lower = {ref.source.lower() for ref in cross_references}

    has_grant      = bool(sources_lower & _GRANT_SOURCES)
    has_corporate  = bool(sources_lower & _CORP_SOURCES)
    has_academic   = bool(sources_lower & _ACADEMIC_SOURCES)
    has_supply     = bool(sources_lower & _SUPPLY_SOURCES)

    # Signal 4: temporal proximity — heuristic: if grant + academic both present
    has_temporal = has_grant and has_academic

    signals = [has_grant, has_corporate, has_academic, has_temporal, has_supply]
    score = sum(20 for s in signals if s)

    # Penalties
    if status.upper() in ("ABANDONED",):
        score -= 30
    if shell_company:
        score -= 20

    return max(0, min(100, score))


def render_score_bar(score: int, width: int = 20) -> str:
    """Return a unicode block progress bar: ████████░░░░ 82/100"""
    filled = int((score / 100) * width)
    empty  = width - filled
    return f"{'█' * filled}{'░' * empty} {score}/100"


def render_signal_dots(refs: List[CrossReference]) -> str:
    """Return source-grouped signal dots: NIH●●●●● SEC●●●●○ DOE○"""
    if not refs:
        return "○○○○○  No signals."

    source_map: dict[str, float] = {}
    for ref in refs:
        src = ref.source.upper()[:6]
        conf = ref.metadata.get("confidence", 100.0)
        # Keep highest confidence per source
        source_map[src] = max(source_map.get(src, 0.0), conf)

    parts = []
    for src, conf in source_map.items():
        filled = min(5, int(conf / 20))
        dots = "●" * filled + "○" * (5 - filled)
        parts.append(f"{src}{dots}")
    return "  ".join(parts)
