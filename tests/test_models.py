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
