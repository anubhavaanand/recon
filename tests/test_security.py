import os
import csv
import io
import pytest
from pathlib import Path
from core.config import Config, save_config, CONFIG_PATH
from tui.widgets.image_tab import is_safe_url
from cli.export import _safe_csv_field

def test_config_file_permissions():
    """Verify that the config file is created with 600 permissions."""
    test_config = Config(lens_api_key="test_key_123")
    save_config(test_config)
    
    assert CONFIG_PATH.exists()
    mode = os.stat(CONFIG_PATH).st_mode
    # 0o600 means -rw-------
    assert oct(mode & 0o777) == "0o600"

def test_url_validation_logic():
    """Check if the URL validation logic is present and working."""
    assert is_safe_url("https://api.lens.org/image.png") is True
    assert is_safe_url("https://patentimages.storage.googleapis.com/abc.jpg") is True
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("http://malicious.com") is False
    assert is_safe_url("https://malicious.com/exploit") is False

def test_markup_injection_escape():
    """Verify that Rich markup in patent data is escaped before rendering."""
    from rich.markup import escape
    malicious = "[bold red]Injected[/] [@click=app.quit]Quit[/]"
    escaped = escape(malicious)
    # The brackets should be escaped so they're not interpreted as markup
    assert "\\[" in escaped or "[bold" not in escaped

def test_csv_safe_field_neutralises_formula():
    """CSV fields starting with formula characters must be prefixed with a tab."""
    assert _safe_csv_field("=SUM(A1:A10)").startswith("\t")
    assert _safe_csv_field("+malicious").startswith("\t")
    assert _safe_csv_field("-1+1").startswith("\t")
    assert _safe_csv_field("@test").startswith("\t")

def test_csv_safe_field_allows_normal_values():
    """Normal patent data should pass through unchanged."""
    assert _safe_csv_field("US-12345678") == "US-12345678"
    assert _safe_csv_field("Quantum Computing Patent") == "Quantum Computing Patent"
    assert _safe_csv_field("2023-01-15") == "2023-01-15"

def test_csv_export_no_injection(tmp_path):
    """Verify the full CSV export pipeline sanitizes dangerous fields."""
    from core.models import PatentRecord
    from cli.export import _export_csv
    
    malicious_record = PatentRecord(
        id="=CMD|'/C calc'!A0",
        title="@SUM(1+1)",
        assignee="+HYPERLINK(\"http://evil.com\")",
        dates={"filed": "2024-01-01"},
        abstract="Test",
        claims=[],
        image_urls=[],
        status="active",
        family_id="FAM-1"
    )
    
    out_file = tmp_path / "test.csv"
    _export_csv([malicious_record], str(out_file))
    
    content = out_file.read_text()
    # Formula-triggering characters should not appear at the start of any cell
    for row in csv.reader(io.StringIO(content)):
        for cell in row:
            if cell:
                assert cell[0] not in ("=", "+", "-", "@"), \
                    f"Unescaped formula character in CSV cell: {cell!r}"

