import pytest

from cli.export import export_pdf, export_records
from core.models import PatentRecord


@pytest.fixture
def sample_records():
    return [
        PatentRecord(id="US1", title="Test Patent 1", assignee="Acme Corp", dates={"filed": "2020-01-01"}, abstract="Abstract 1", claims=["Claim 1"], image_urls=[], status="active", family_id="F1"),
        PatentRecord(id="US2", title="Test Patent 2", assignee="Globex Inc", dates={"filed": "2021-01-01"}, abstract="Abstract 2", claims=["Claim A", "Claim B"], image_urls=[], status="active", family_id="F2"),
    ]

def test_export_csv(sample_records, tmp_path):
    output_file = tmp_path / "test.csv"
    export_records(sample_records, "csv", str(output_file))
    content = output_file.read_text()
    assert "Test Patent 1" in content
    assert "Acme Corp" in content

def test_export_json(sample_records, tmp_path):
    output_file = tmp_path / "test.json"
    export_records(sample_records, "json", str(output_file))
    content = output_file.read_text()
    assert '"US1"' in content
    assert '"Globex Inc"' in content

def test_export_bibtex(sample_records, tmp_path):
    output_file = tmp_path / "test.bib"
    export_records(sample_records, "bibtex", str(output_file))
    content = output_file.read_text()
    assert "@patent{US1" in content
    assert "author = {Acme Corp}" in content

def test_export_markdown(sample_records, tmp_path):
    output_file = tmp_path / "test.md"
    export_records(sample_records, "markdown", str(output_file))
    content = output_file.read_text()
    assert "# Test Patent 1" in content
    assert "**Assignee**: Acme Corp" in content

def test_export_pdf(sample_records, tmp_path):
    output_file = tmp_path / "test.pdf"
    export_records(sample_records, "pdf", str(output_file))
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    # Read binary header
    with open(output_file, 'rb') as f:
        header = f.read(4)
        assert header == b"%PDF"

def test_export_pdf_via_function(sample_records, tmp_path):
    """Test the dedicated export_pdf function with title page and claims."""
    output_file = tmp_path / "patents.pdf"
    export_pdf(sample_records, str(output_file))

    # Verify file exists and is valid PDF
    assert output_file.exists()
    pdf_size = output_file.stat().st_size
    assert pdf_size > 2000  # Title page + 2 patent pages should be > 2KB

    with open(output_file, 'rb') as f:
        header = f.read(4)
        assert header == b"%PDF"

    # Verify PDF structure: should have 1 title page + 2 patent pages (3 total)
    # The /Count entry in the PDF should show 3 pages
    pdf_content = output_file.read_bytes()
    assert b"/Count 3" in pdf_content  # Verify 3 pages were created
    assert b"/Type /Pages" in pdf_content  # Valid PDF page structure

def test_export_pdf_empty_collection(tmp_path):
    """Verify export_pdf rejects empty collections."""
    output_file = tmp_path / "empty.pdf"
    with pytest.raises(ValueError, match="empty collection"):
        export_pdf([], str(output_file))
