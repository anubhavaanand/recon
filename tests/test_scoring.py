import pytest
from core.scoring import calculate_signal_score, match_entity
from core.models import CrossReference

def test_entity_matching():
    # Exact match
    assert match_entity("Acme Corp", "Acme Corp") == 100.0
    
    # Fuzzy match
    assert match_entity("Acme Corporation", "Acme Corp") >= 85.0
    
    # Non-match
    assert match_entity("Acme Corporation", "Globex Inc") < 85.0

def test_equal_weight_scoring():
    # 0 signals -> 0
    assert calculate_signal_score([]) == 0
    
    # 1 grant signal -> 20
    refs = [CrossReference(source="NIH", url="")]
    assert calculate_signal_score(refs) == 20
    
    # All 5 distinct signal types -> 100
    # grant(NIH) + corp(SEC) + academic(OpenAlex) + temporal(NIH+OA) + supply(opencorporates) = 5
    refs = [
        CrossReference(source="NIH", url=""),          # grant
        CrossReference(source="SEC", url=""),          # corp
        CrossReference(source="OpenAlex", url=""),     # academic (also triggers temporal with NIH)
        CrossReference(source="opencorporates", url=""),  # supply chain
    ]
    score = calculate_signal_score(refs)
    assert score == 100  # 5 signals x 20 = 100
    
    # Extra refs beyond 5 types -> still capped at 100
    refs.append(CrossReference(source="arXiv", url=""))
    assert calculate_signal_score(refs) == 100
