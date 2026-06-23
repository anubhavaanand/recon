from core.models import PatentRecord, CrossReference

def test_models():
    cr = CrossReference(source="NSF", url="http://example.com")
    assert cr.weight == 1.0

    record = PatentRecord(
        id="US1234567A",
        title="Test Patent",
        assignee="Test Corp",
        dates={"filing": "2020-01-01"},
        abstract="Test Abstract",
        claims=["Claim 1"],
        image_urls=[],
        status="Active",
        family_id="F123",
        cross_references=[cr]
    )
    assert record.id == "US1234567A"
    assert len(record.cross_references) == 1
    assert record.cross_references[0].source == "NSF"


def test_patent_record_text_cleanup():
    record = PatentRecord(
        id="US-1234567_A",
        title="TestTitleSpacing",
        assignee="TestCorpChinese本发明",
        dates={},
        abstract="AbstractTranslated fromChinese本发明涉及一种航空发动机。The invention relates to an engine.",
        claims=["Claim1AbstractTranslated", "本发明The invention"],
        image_urls=[],
        status="Active",
        family_id="F123",
    )
    # Check ID normalized
    assert record.id == "US1234567A"
    # Check spacing fixes
    assert record.title == "Test Title Spacing"
    assert record.assignee == "Test Corp Chinese 本发明"
    assert record.abstract == "Abstract: Translated from Chinese 本发明涉及一种航空发动机。 The invention relates to an engine."
    assert record.claims == ["Claim 1 Abstract: Translated", "本发明 The invention"]

