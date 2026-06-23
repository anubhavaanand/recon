"""Inline slash command palette for RECON.

When user types / in the search input, this widget shows available commands
filtered by fuzzy match. Keyboard: ↑/↓ navigate, Enter execute, Esc dismiss.
Uses inline Static with hidden CSS class (no ModalScreen — constitution-compliant).
"""

from __future__ import annotations

from rich.markup import escape
from textual.widgets import Static
from rapidfuzz import fuzz


SLASH_COMMANDS = [
    ("/search",    "Search patents",          "focus_search"),
    ("/export",    "Export collection",       "export_collection"),
    ("/save",      "Save current patent",     "save_collection"),
    ("/reader",    "Open reader mode",        "reader_mode"),
    ("/cite",      "Show citation graph",     "show_citation_graph"),
    ("/translate", "Toggle translation",      "translate"),
    ("/source",    "Filter sources",          "toggle_source_filter"),
    ("/help",      "Show help",               "toggle_help"),
    ("/clear",     "Clear search",            "clear_search"),
    ("/config",    "Show config",             "show_config"),
    ("/quit",      "Quit RECON",              "quit"),
]


class CommandPalette(Static):
    """Inline command palette dropdown, toggled via hidden CSS class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands: list[tuple[str, str, str]] = SLASH_COMMANDS
        self._filtered: list[tuple[str, str, str]] = SLASH_COMMANDS
        self._selected: int = 0
        self._active: bool = False

    def filter(self, query: str) -> None:
        """Filter commands by fuzzy match on query."""
        if not query or query == "/":
            self._filtered = list(self._commands)
        else:
            q = query.lstrip("/").lower()
            scored = []
            for cmd, desc, action in self._commands:
                score = fuzz.partial_ratio(q, cmd.lstrip("/"))
                if score > 30:
                    scored.append((score, cmd, desc, action))
            scored.sort(key=lambda x: x[0], reverse=True)
            self._filtered = [(c, d, a) for _, c, d, a in scored]
        self._selected = 0
        self._render()

    def select_next(self) -> None:
        if self._filtered:
            self._selected = (self._selected + 1) % len(self._filtered)
            self._render()

    def select_prev(self) -> None:
        if self._filtered:
            self._selected = (self._selected - 1) % len(self._filtered)
            self._render()

    def selected_action(self) -> str | None:
        if self._filtered and 0 <= self._selected < len(self._filtered):
            return self._filtered[self._selected][2]
        return None

    def _render(self) -> None:
        lines = []
        for i, (cmd, desc, _) in enumerate(self._filtered):
            marker = "\u25b8" if i == self._selected else " "
            lines.append(f" {marker} {escape(cmd):<12} {escape(desc)}")
        if not lines:
            lines.append(" No matching commands")
        self.update("\n".join(lines))

    @property
    def is_active(self) -> bool:
        return self._active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._active = value
        if value:
            self._filtered = list(self._commands)
            self._selected = 0
            self._render()
