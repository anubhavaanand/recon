import pytest
from unittest.mock import AsyncMock, patch
import httpx
from core.intelligence import SynthesisEngine
from core.models import PatentRecord

@pytest.mark.asyncio
async def test_query_ollama_success():
    engine = SynthesisEngine(model="test-model")
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "This is a summary."}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await engine._query_ollama("Test prompt")
        assert result == "This is a summary."

@pytest.mark.asyncio
async def test_query_ollama_failure():
    engine = SynthesisEngine()
    
    mock_response = AsyncMock()
    mock_response.status_code = 500
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await engine._query_ollama("Test prompt")
        assert "ERR: Ollama returned 500" in result

@pytest.mark.asyncio
async def test_summarize_results_empty():
    engine = SynthesisEngine()
    result = await engine.summarize_results([])
    assert "No records" in result

@pytest.mark.asyncio
async def test_summarize_results_mocked():
    engine = SynthesisEngine()
    record = PatentRecord(id="P1", title="T1", abstract="A1", assignee="C1", dates={}, status="A")
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Grouped summary."}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await engine.summarize_results([record])
        assert result == "Grouped summary."

@pytest.mark.asyncio
async def test_translate_text_mocked():
    engine = SynthesisEngine()
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Translation text."}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await engine.translate_text("Original text", target_lang="German")
        assert result == "Translation text."
