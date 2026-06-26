import pytest

from core.config import Config
from tui.app import ReconApp
from tui.screens import SearchScreen

try:
    from tui.screens import TerminalDetectionScreen
except ImportError:
    TerminalDetectionScreen = None

@pytest.mark.asyncio
async def test_first_run_shows_detection_screen(monkeypatch):
    # Mock config so terminal_detection_seen is False
    monkeypatch.setattr("core.config.load_config", lambda: Config(terminal_detection_seen=False))

    app = ReconApp()
    async with app.run_test():
        # Should push TerminalDetectionScreen
        if TerminalDetectionScreen:
            assert isinstance(app.screen, TerminalDetectionScreen), "Expected TerminalDetectionScreen to be active."
        else:
            pytest.fail("TerminalDetectionScreen is not implemented.")

@pytest.mark.asyncio
async def test_subsequent_run_shows_search_screen(monkeypatch):
    # Mock config so terminal_detection_seen is True
    monkeypatch.setattr("core.config.load_config", lambda: Config(terminal_detection_seen=True))

    app = ReconApp()
    async with app.run_test():
        # Should push SearchScreen
        assert isinstance(app.screen, SearchScreen), "Expected SearchScreen to be active."
