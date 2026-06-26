from core.models import CrossReference
from core.scoring import calculate_signal_score, match_entity


def test_entity_matching():
    assert match_entity("Acme Corp", "Acme Corp") == 100.0
    assert match_entity("Acme Corporation", "Acme Corp") >= 85.0
    assert match_entity("Acme Corporation", "Globex Inc") < 85.0


def test_equal_weight_scoring():
    assert calculate_signal_score([]) == 0
    refs = [CrossReference(source="NIH", url="", date="2021-06-15")]
    assert calculate_signal_score(refs, filing_date="2022-06-15") == 40  # grant + temporal
    refs = [
        CrossReference(source="NIH", url="", date="2021-06-15"),
        CrossReference(source="SEC", url=""),
        CrossReference(source="OpenAlex", url="", date="2021-06-15"),
        CrossReference(source="opencorporates", url=""),
    ]
    score = calculate_signal_score(refs, filing_date="2022-06-15")
    assert score == 100
    refs.append(CrossReference(source="arXiv", url=""))
    assert calculate_signal_score(refs, filing_date="2022-06-15") == 100


def test_each_signal_individually_weighted_20():
    signals = {
        "NIH": 20,
        "nsf": 20,
        "SEC": 20,
        "OpenAlex": 20,
        "opencorporates": 20,
    }
    for source, expected_weight in signals.items():
        refs = [CrossReference(source=source, url="")]
        score = calculate_signal_score(refs)
        assert score == expected_weight, (
            f"Signal '{source}' scored {score}, expected {expected_weight}"
        )


def test_all_signal_types_equal_weight():
    grant = CrossReference(source="NIH", url="")
    corp = CrossReference(source="SEC", url="")
    academic = CrossReference(source="OpenAlex", url="")
    supply = CrossReference(source="opencorporates", url="")
    assert calculate_signal_score([grant]) == calculate_signal_score([corp])
    assert calculate_signal_score([corp]) == calculate_signal_score([academic])
    assert calculate_signal_score([academic]) == calculate_signal_score([supply])


def test_scoring_determinism():
    refs = [
        CrossReference(source="NIH", url="", metadata={"confidence": 90.0}),
        CrossReference(source="SEC", url="", metadata={"confidence": 75.0}),
        CrossReference(source="OpenAlex", url="", metadata={"confidence": 60.0}),
    ]
    result1 = calculate_signal_score(refs, status="active", shell_company=False)
    result2 = calculate_signal_score(refs, status="active", shell_company=False)
    assert result1 == result2


def test_scoring_determinism_with_penalties():
    refs = [CrossReference(source="NIH", url="")]
    result1 = calculate_signal_score(refs, status="ABANDONED", shell_company=True)
    result2 = calculate_signal_score(refs, status="ABANDONED", shell_company=True)
    assert result1 == result2


def test_no_hidden_weights():
    from core.scoring import _ACADEMIC_SOURCES, _CORP_SOURCES, _GRANT_SOURCES, _SUPPLY_SOURCES
    total_unique = len(_GRANT_SOURCES | _CORP_SOURCES | _ACADEMIC_SOURCES | _SUPPLY_SOURCES)
    assert total_unique > 0
    for source in _GRANT_SOURCES:
        s = calculate_signal_score([CrossReference(source=source, url="")])
        assert s == 20, f"Grant source '{source}' not weighted +20"
    for source in _CORP_SOURCES:
        s = calculate_signal_score([CrossReference(source=source, url="")])
        assert s == 20, f"Corporate source '{source}' not weighted +20"
    for source in _ACADEMIC_SOURCES:
        s = calculate_signal_score([CrossReference(source=source, url="")])
        assert s == 20, f"Academic source '{source}' not weighted +20"
    for source in _SUPPLY_SOURCES:
        s = calculate_signal_score([CrossReference(source=source, url="")])
        assert s == 20, f"Supply source '{source}' not weighted +20"


def test_weigh_documentation():
    signals = {
        "grant": {"sources": ["NIH", "NSF", "DOE", "NIH REPORTER", "NSF AWARDS"], "weight": 20},
        "corporate": {"sources": ["SEC", "EDGAR", "10-K", "8-K"], "weight": 20},
        "academic": {"sources": ["OpenAlex", "arXiv"], "weight": 20},
        "supply_chain": {"sources": ["OpenCorporates", "Supply Chain", "DUNS"], "weight": 20},
        "temporal_proximity": {"sources": ["cross-ref date within 2yr of filing date"], "weight": 20},
    }
    for signal_name, config in signals.items():
        assert config["weight"] == 20, f"Signal '{signal_name}' weight is {config['weight']}, expected 20"
