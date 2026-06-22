# RECON Test Fixtures

This directory contains test data and mock responses used by the RECON evaluation framework.

## Current State

Fixtures are defined inline within test files using `pytest.fixture` decorators, `unittest.mock`, and `tmp_path` for temporary file operations. No static fixture files are currently required.

## Test Data Sources

### Mock Patent Records

Created inline in test files using `PatentRecord` dataclass:

```python
from core.models import PatentRecord

record = PatentRecord(
    id="US12345678",
    title="Test Patent",
    assignee="ACME Corp",
    dates={"filed": "2020-01-01", "granted": "2022-06-15"},
    abstract="A test patent abstract.",
    claims=["Claim 1: A method.", "Claim 2: The method of claim 1."],
    image_urls=["https://patentimages.storage.googleapis.com/img1.png"],
    status="active",
    family_id="FAM001",
)
```

### Mock API Responses

API mocking uses `unittest.mock.AsyncMock` and `monkeypatch` (pytest fixture):

```python
from unittest.mock import AsyncMock, patch

with patch("clients.patent_apis.USPTOClient.search") as mock:
    mock.return_value = [record]
    results = await search_all("test query")
```

### Terminal Capability Mocks

Terminal detection is mocked via environment variables:

```python
with patch.dict(os.environ, {"TERM": "xterm-kitty"}):
    protocol = detect_terminal_protocol()
    assert protocol == TerminalProtocol.KITTY
```

### Error Scenario Responses

Error injection uses `unittest.mock`:

```python
from unittest.mock import patch

with patch("httpx.AsyncClient.get") as mock_get:
    mock_get.side_effect = httpx.TimeoutException("Connection timed out")
    # Test error handling
```

## How to Add New Fixtures

1. **Simple records**: Create inline in your test file
2. **Reusable records**: Add a `@pytest.fixture` in `tests/conftest.py` (create if not exists)
3. **Static fixture files**: Add JSON/TOML files to this directory and load them in tests

## Fixture Naming Convention

- `mock_*` for unittest.mock objects
- `sample_*` for sample PatentRecord instances
- `test_*` prefix for test functions (pytest convention)

## Related Files

- `tests/` - All test modules
- `tests/health_check.py` - Standalone health check script
- `tests/evaluation_report.py` - Evaluation report generator
