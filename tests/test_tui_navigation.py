import pytest

from core.models import PatentRecord
from tui.app import ReconApp
from tui.screens import ReaderModeScreen, SearchScreen


@pytest.mark.asyncio
async def test_textual_list_navigation_speed():
    app = ReconApp()
    async with app.run_test() as pilot:
        # Simulate loading search results
        await pilot.press("enter")

        # Test navigation update speed
        # Ideally, wait for next frame and ensure it's < 100ms
        import time
        start = time.perf_counter()
        await pilot.press("down")
        end = time.perf_counter()

        duration_ms = (end - start) * 1000
        assert duration_ms < 100, f"Navigation took {duration_ms}ms, which is > 100ms"


@pytest.mark.asyncio
async def test_reader_mode_screen_keyboard_bindings():
    """Test ReaderModeScreen has proper keyboard bindings for reader mode."""
    record = PatentRecord(
        id="US123456",
        title="Test Patent",
        assignee="ACME Corp",
        dates={"filed": "2020-01-01"},
        abstract="Test abstract",
        claims=["Claim 1", "Claim 2"],
        image_urls=[],
        status="active",
        family_id="FAMILY123"
    )
    screen = ReaderModeScreen(record)
    assert ("q", "app.pop_screen", "Quit") in screen.BINDINGS
    assert ("j", "scroll_down", "Down") in screen.BINDINGS
    assert ("k", "scroll_up", "Up") in screen.BINDINGS


def test_search_screen_export_binding():
    """Test SearchScreen has export_collection keyboard shortcut."""
    screen = SearchScreen()
    binding_keys = [(b[0], b[1]) for b in screen.BINDINGS]
    assert ("e", "export_collection") in binding_keys


def test_search_screen_download_binding():
    """Test SearchScreen has download_patent keyboard shortcut."""
    screen = SearchScreen()
    binding_keys = [(b[0], b[1]) for b in screen.BINDINGS]
    assert ("d", "download_patent") in binding_keys


def test_search_screen_focus_search_binding():
    """Test SearchScreen has focus_search keyboard shortcut."""
    screen = SearchScreen()
    binding_keys = [(b[0], b[1]) for b in screen.BINDINGS]
    assert ("/", "focus_search") in binding_keys


def test_search_screen_help_binding():
    """Test SearchScreen has toggle_help keyboard shortcut."""
    screen = SearchScreen()
    binding_keys = [(b[0], b[1]) for b in screen.BINDINGS]
    assert ("?", "toggle_help") in binding_keys


def test_help_overlay_initial_state():
    """Test that help overlay is initially hidden in SearchScreen."""
    screen = SearchScreen()
    # _show_help is the internal attribute name in the new implementation
    assert hasattr(screen, '_show_help')
    assert screen._show_help is False


def test_reader_mode_has_correct_bindings():
    """Test that ReaderModeScreen has bindings without Header/Footer."""
    record = PatentRecord(
        id="US123456",
        title="Test Patent",
        assignee="ACME Corp",
        dates={"filed": "2020-01-01"},
        abstract="Test abstract",
        claims=["Claim 1"],
        image_urls=[],
        status="active",
        family_id="FAMILY123"
    )
    screen = ReaderModeScreen(record)

    # Check that proper bindings exist (no Back to Search, just Quit and scroll)
    assert ("q", "app.pop_screen", "Quit") in screen.BINDINGS
    assert ("j", "scroll_down", "Down") in screen.BINDINGS
    assert ("k", "scroll_up", "Up") in screen.BINDINGS


def test_reader_mode_status_line_method():
    """Test that ReaderModeScreen has status line builder method."""
    record = PatentRecord(
        id="US123456",
        title="Test Patent",
        assignee="ACME Corp",
        dates={"filed": "2020-01-01"},
        abstract="Test abstract",
        claims=["Claim 1"],
        image_urls=[],
        status="active",
        family_id="FAMILY123"
    )
    screen = ReaderModeScreen(record)

    # _build_content includes id and abstract; title is in the header line
    content = screen._build_content()
    assert "US123456" in content
    assert "Test abstract" in content
