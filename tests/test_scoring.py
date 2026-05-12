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
    
    # 1 signal -> 20
    refs = [CrossReference(source="NIH", url="")]
    assert calculate_signal_score(refs) == 20
    
    # 5 signals -> 100
    refs = [
        CrossReference(source="NIH", url=""),
        CrossReference(source="NSF", url=""),
        CrossReference(source="SEC", url=""),
        CrossReference(source="OpenAlex", url=""),
        CrossReference(source="arXiv", url="")
    ]
    assert calculate_signal_score(refs) == 100
    
    # 6 signals -> still 100 (max)
    refs.append(CrossReference(source="OpenCorporates", url=""))
    assert calculate_signal_score(refs) == 100
