import pytest

from core.translation import _cache_key, _is_non_english, translate_text


class TestIsNonEnglish:
    def test_english_ascii_only(self):
        assert _is_non_english("Hello world this is English text") is False

    def test_english_with_punctuation(self):
        assert _is_non_english("Patent: a novel battery technology.") is False

    def test_chinese_detected(self):
        assert _is_non_english("一种固态电池电解质材料") is True

    def test_japanese_detected(self):
        assert _is_non_english("固体電池の電解質材料") is True

    def test_korean_detected(self):
        assert _is_non_english("고체 배터리 전해질") is True

    def test_cyrillic_detected(self):
        assert _is_non_english("Твердотельный аккумулятор") is True

    def test_german_with_umlaut_is_european(self):
        assert _is_non_english("Festkörperbatterie Elektrolyt") is False

    def test_empty_string(self):
        assert _is_non_english("") is False

    def test_unknown_placeholder(self):
        assert _is_non_english("[?]") is False
        assert _is_non_english("UNKNOWN") is False

    def test_mixed_with_mostly_english(self):
        # Less than 5% non-ASCII threshold
        text = "This is English with one café"
        assert _is_non_english(text) is False


class TestCacheKey:
    def test_cache_key_is_deterministic(self):
        assert _cache_key("hello") == _cache_key("hello")

    def test_cache_key_differs_for_diff_text(self):
        assert _cache_key("hello") != _cache_key("world")

    def test_cache_key_length(self):
        assert len(_cache_key("test")) == 16


@pytest.mark.asyncio
async def test_translate_text_returns_same_for_english():
    """English text should pass through unchanged."""
    result = await translate_text("This is a patent abstract about batteries.")
    assert result == "This is a patent abstract about batteries."


@pytest.mark.asyncio
async def test_translate_text_returns_same_for_unknown():
    """Placeholder values should pass through unchanged."""
    assert await translate_text("") == ""
    assert await translate_text("[?]") == "[?]"
    assert await translate_text("UNKNOWN") == "UNKNOWN"


@pytest.mark.asyncio
async def test_translate_text_handles_ollama_unreachable(monkeypatch):
    """When Ollama is unreachable, return original text gracefully."""
    async def mock_post(*args, **kwargs):
        raise Exception("Connection refused")

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    result = await translate_text("一种固态电池电解质材料")
    assert result == "一种固态电池电解质材料"


@pytest.mark.asyncio
async def test_translate_text_handles_ollama_timeout(monkeypatch):
    """When Ollama times out, return original text gracefully."""

    async def mock_post(*args, **kwargs):
        from httpx import TimeoutException
        raise TimeoutException("Timed out")

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    result = await translate_text("固体電池の電解質材料")
    assert result == "固体電池の電解質材料"


@pytest.mark.asyncio
async def test_translate_text_handles_ollama_404(monkeypatch):
    """When model not found, return original text."""

    async def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 404
            async def json(self):
                return {}
            def raise_for_status(self):
                raise Exception("404")

        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    result = await translate_text("一种固态电池电解质材料")
    assert result == "一种固态电池电解质材料"


@pytest.mark.asyncio
async def test_translate_skips_already_translated():
    """Text that already has [t] prefix should be skipped."""
    result = await translate_text("[t]Solid state battery electrolyte")
    assert result == "[t]Solid state battery electrolyte"
