"""
TUI layout tests using Textual's async pilot framework.
PRD §10: TUI tests using Textual's async pilot framework.
"""
import pytest
from textual.widgets import Input, Static, ListView


@pytest.mark.asyncio
async def test_search_screen_mounts():
    """SearchScreen composes without errors."""
    from tui.app import ReconApp
    async with ReconApp().run_test(size=(140, 40)) as pilot:
        await pilot.pause(0.3)
        screen = pilot.app.screen
        assert screen.__class__.__name__ in ("SearchScreen", "TerminalDetectionScreen")


@pytest.mark.asyncio
async def test_search_returns_results():
    """Searching 'quantum' populates result list."""
    from tui.app import ReconApp
    from tui.screens import SearchScreen
    async with ReconApp().run_test(size=(140, 40)) as pilot:
        await pilot.app.switch_screen(SearchScreen())
        await pilot.pause(0.5)
        await pilot.click("#search_input")
        for ch in "quantum":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause(3.0)
        screen = pilot.app.screen
        result_list = screen.query_one("#result_list")
        # item_count or len(children) — check results loaded
        children = list(result_list.children)
        assert len(children) > 0


@pytest.mark.asyncio
async def test_tab_switching_hl():
    """h/l keys switch preview tabs."""
    from tui.app import ReconApp
    from tui.screens import SearchScreen
    async with ReconApp().run_test(size=(140, 40)) as pilot:
        await pilot.app.switch_screen(SearchScreen())
        await pilot.pause(1.0)
        # Search first to get results
        await pilot.click("#search_input")
        for ch in "battery":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause(4.0)
        
        # Blur the input so character keys bubble up to the screen bindings
        pilot.app.screen.query_one("#search_input").blur()
        await pilot.pause(3.0)
        
        screen = pilot.app.screen
        screen.refresh()
        assert screen._active_tab == "info"
        await pilot.press("l")
        await pilot.pause(4.0)
        screen.refresh()
        assert screen._active_tab == "claims"
        await pilot.press("l")
        await pilot.pause(4.0)
        screen.refresh()
        assert screen._active_tab == "image"
        await pilot.press("h")
        await pilot.pause(4.0)
        screen.refresh()
        assert screen._active_tab == "claims"


@pytest.mark.asyncio
async def test_help_overlay_toggle():
    """? key toggles the help overlay visibility."""
    from tui.app import ReconApp
    from tui.screens import SearchScreen
    from textual.widgets import Static
    async with ReconApp().run_test(size=(140, 40)) as pilot:
        await pilot.app.switch_screen(SearchScreen())
        await pilot.pause(1.5)
        
        # Blur input to let '?' bubble
        pilot.app.screen.query_one("#search_input").blur()
        await pilot.pause(1.0)
        
        screen = pilot.app.screen
        overlay = screen.query_one("#help_overlay", Static)
        assert "hidden" in overlay.classes  # starts hidden
        
        await pilot.press("?")
        await pilot.pause(2.0)
        assert "hidden" not in overlay.classes
        
        await pilot.press("?")
        await pilot.pause(2.0)
        assert "hidden" in overlay.classes


@pytest.mark.asyncio
async def test_reader_mode_push():
    """r key pushes ReaderModeScreen when a result is selected."""
    from tui.app import ReconApp
    from tui.screens import SearchScreen, ReaderModeScreen
    async with ReconApp().run_test(size=(140, 40)) as pilot:
        await pilot.app.switch_screen(SearchScreen())
        await pilot.pause(1.5)
        await pilot.click("#search_input")
        for ch in "quantum":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause(4.0)
        
        # Blur input so 'r' bubbles
        pilot.app.screen.query_one("#search_input").blur()
        await pilot.pause(1.0)
        
        # Navigate to first result and focus it
        result_list = pilot.app.screen.query_one("#result_list")
        result_list.focus()
        await pilot.press("down")
        await pilot.pause(1.0)
        
        await pilot.press("r")
        await pilot.pause(2.5)
        assert isinstance(pilot.app.screen, ReaderModeScreen)


@pytest.mark.asyncio
async def test_theme_validation():
    """Submitting /theme commands updates status or changes classes on SearchScreen."""
    from tui.app import ReconApp
    from tui.screens import SearchScreen
    async with ReconApp().run_test(size=(140, 40)) as pilot:
        await pilot.app.switch_screen(SearchScreen())
        await pilot.pause(0.5)

        # 1. Invalid theme /theme invalid should show error
        await pilot.click("#search_input")
        for ch in "/theme invalid":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause(0.5)
        
        status_top = pilot.app.screen.query_one("#status_top", Static)
        assert "ERR: Choose theme" in str(status_top.content)

        # 2. Valid theme /theme arctic-frost should apply class and clear input
        search_input = pilot.app.screen.query_one("#search_input", Input)
        search_input.value = ""
        await pilot.click("#search_input")
        for ch in "/theme arctic-frost":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause(0.5)
        
        assert "theme-arctic-frost" in pilot.app.screen.classes
        assert search_input.value == ""


@pytest.mark.asyncio
async def test_assignee_view_toggle():
    """a key toggles the assignee portfolio view overlay and builds it with correct width."""
    from tui.app import ReconApp
    from tui.screens import SearchScreen
    async with ReconApp().run_test(size=(140, 40)) as pilot:
        await pilot.app.switch_screen(SearchScreen())
        await pilot.pause(0.5)
        
        pilot.app.screen.query_one("#search_input").blur()
        await pilot.pause(0.1)
        
        screen = pilot.app.screen
        overlay = screen.query_one("#assignee_overlay", Static)
        assert "hidden" in overlay.classes
        
        await pilot.press("a")
        await pilot.pause(0.5)
        assert "hidden" not in overlay.classes
        
        content_lines = str(overlay.content).splitlines()
        assert len(content_lines[0]) == len(content_lines[1])
        
        await pilot.press("a")
        await pilot.pause(0.5)
        assert "hidden" in overlay.classes
