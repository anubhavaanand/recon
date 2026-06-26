import pytest

from core.models import CrossReference, PatentRecord


@pytest.fixture
def sample_record() -> PatentRecord:
    return PatentRecord(
        id="US12345678B2",
        title="Test Patent for Solid State Battery",
        assignee="ACME Corp",
        dates={"filed": "2022-06-15", "expires": "2042-06-15", "family_count": "3"},
        abstract="A solid state battery with improved electrolyte stability.",
        claims=[
            "A solid state battery comprising: an anode, a cathode, and a solid electrolyte.",
            "The battery of claim 1, wherein the solid electrolyte is a ceramic.",
            "The battery of claim 1, wherein the anode comprises lithium metal.",
        ],
        image_urls=["https://patentimages.storage.googleapis.com/img1.png"],
        status="active",
        family_id="FAM001",
    )


@pytest.fixture
def sample_cross_references() -> list[CrossReference]:
    return [
        CrossReference(source="NIH", url="https://reporter.nih.gov/project/123", metadata={"confidence": 90.0}),
        CrossReference(source="SEC", url="https://sec.gov/filing/abc", metadata={"confidence": 75.0}),
        CrossReference(source="OpenAlex", url="https://openalex.org/work/W321", metadata={"confidence": 60.0}),
    ]


@pytest.fixture
def sample_record_with_signals(sample_record, sample_cross_references) -> PatentRecord:
    sample_record.cross_references = sample_cross_references
    return sample_record


@pytest.fixture
def tmp_cache_db(tmp_path) -> str:
    db_path = tmp_path / "test_recon_cache.db"
    return str(db_path)


@pytest.fixture
def mock_patent_records() -> list[PatentRecord]:
    return [
        PatentRecord(
            id=f"US{i}",
            title=f"Patent {i}",
            assignee="Test Corp",
            dates={"filed": f"202{i}-01-01"},
            abstract=f"Abstract for patent {i}.",
            claims=[], image_urls=[], status="active", family_id="F",
        )
        for i in range(5)
    ]
