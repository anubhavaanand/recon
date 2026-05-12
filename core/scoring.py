from rapidfuzz import fuzz
from typing import List
from core.models import CrossReference

def match_entity(entity1: str, entity2: str) -> float:
    """
    Returns deterministic similarity score between two entities.
    Exact match is 100.
    """
    if entity1.lower() == entity2.lower():
        return 100.0
    return fuzz.partial_ratio(entity1, entity2)

def calculate_signal_score(cross_references: List[CrossReference]) -> int:
    """
    Calculates score based purely on presence of signals.
    Each signal adds +20 points. Maximum 100 points.
    """
    return min(len(cross_references) * 20, 100)
