import pytest
from core.arbitrage import calculate_arbitrage_status, render_arbitrage_table
from core.models import PatentRecord

def test_arbitrage_status_deterministic():
    record = PatentRecord(
        id="US2023001",
        title="Test Patent",
        abstract="Test abstract",
        assignee="Test Corp",
        dates={"filed": "2023-01-01"},
        status="ACTIVE"
    )
    status1 = calculate_arbitrage_status(record)
    status2 = calculate_arbitrage_status(record)
    
    assert status1 == status2
    assert "US" in status1
    assert status1["US"] == "ACTIVE"

def test_arbitrage_status_variation():
    record1 = PatentRecord(id="US1", title="T1", abstract="A1", assignee="X", dates={}, status="A")
    record2 = PatentRecord(id="EP2", title="T2", abstract="A2", assignee="Y", dates={}, status="A")
    
    status1 = calculate_arbitrage_status(record1)
    status2 = calculate_arbitrage_status(record2)
    
    assert status1["US"] == "ACTIVE"
    assert status2["EP"] == "ACTIVE"
    # Even though simulated, different IDs should yield different hashes/status maps
    assert status1 != status2

def test_render_table_format():
    status_map = {"US": "ACTIVE", "EP": "PENDING", "CN": "NO_FILING"}
    table = render_arbitrage_table(status_map)
    
    assert "US" in table
    assert "ACTIVE" in table
    assert "PENDING" in table
    assert "CN" in table
    assert "────────" in table # Separator
