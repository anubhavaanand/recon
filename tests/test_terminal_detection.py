import pytest

from core.config import Config
from tui.app import ReconApp
from tui.screens import SearchScreen, TerminalDetectionScreen


@pytest.mark.asyncio
async def test_first_run_shows_detection_screen(monkeypatch):
    monkeypatch.setattr("core.config.load_config", lambda: Config(terminal_detection_seen=False))

    app = ReconApp()
    async with app.run_test():
        assert isinstance(app.screen, TerminalDetectionScreen), "Expected TerminalDetectionScreen on first run."


@pytest.mark.asyncio
async def test_subsequent_run_shows_search_screen(monkeypatch):
    monkeypatch.setattr("core.config.load_config", lambda: Config(terminal_detection_seen=True))

    app = ReconApp()
    async with app.run_test():
        assert isinstance(app.screen, SearchScreen), "Expected SearchScreen when detection already seen."
