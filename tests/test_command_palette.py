"""Tests for the inline slash command palette (Phase 3)."""

from tui.widgets.command_palette import CommandPalette, SLASH_COMMANDS


def test_filter_all_commands_on_slash():
    """filter("/") returns all 11 commands."""
    palette = CommandPalette()
    palette.filter("/")
    assert len(palette._filtered) == 12
    assert palette._filtered == SLASH_COMMANDS


def test_filter_fuzzy_matches():
    """filter("/sea") includes "/search" in filtered results."""
    palette = CommandPalette()
    palette.filter("/sea")
    actions = [action for _, _, action in palette._filtered]
    assert "focus_search" in actions


def test_select_next_cycles():
    """select_next() moves selection to the next item."""
    palette = CommandPalette()
    palette.filter("/")
    assert palette._selected == 0
    palette.select_next()
    assert palette._selected == 1
    assert palette.selected_action() == SLASH_COMMANDS[1][2]


def test_select_prev_wraps():
    """select_prev() at index 0 wraps to the last command."""
    palette = CommandPalette()
    palette.filter("/")
    assert palette._selected == 0
    palette.select_prev()
    last_index = len(SLASH_COMMANDS) - 1
    assert palette._selected == last_index
    assert palette.selected_action() == SLASH_COMMANDS[last_index][2]


def test_selected_action_returns_correct_action():
    """After filter("/exp"), selected_action() returns 'export_collection'."""
    palette = CommandPalette()
    palette.filter("/exp")
    assert palette.selected_action() == "export_collection"


def test_escape_dismisses():
    """is_active = False hides the palette."""
    palette = CommandPalette()
    assert palette.is_active is False

    palette.is_active = True
    assert palette.is_active is True
    assert len(palette._filtered) == 12  # reset on activation

    palette.is_active = False
    assert palette.is_active is False
