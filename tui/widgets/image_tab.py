import os
import asyncio
import subprocess
from enum import Enum
from urllib.parse import urlparse

from rich.markup import escape
from textual.widgets import Static
from core.models import PatentRecord


class TerminalProtocol(Enum):
    KITTY   = "Kitty"
    ITERM2  = "iTerm2"
    SIXEL   = "Sixel"
    FALLBACK = "Fallback (external viewer)"


def detect_terminal_protocol() -> TerminalProtocol:
    term         = os.environ.get("TERM", "").lower()
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    kitty_window = os.environ.get("KITTY_WINDOW_ID", "")
    mlterm_flag  = os.environ.get("MLTERM", "")

    if kitty_window:
        return TerminalProtocol.KITTY
    if "iterm" in term_program or "wezterm" in term_program:
        return TerminalProtocol.ITERM2
    if "mlterm" in term or mlterm_flag:
        return TerminalProtocol.SIXEL
    return TerminalProtocol.FALLBACK


# Trusted patent image domains (security: prevent open redirect)
_ALLOWED_DOMAINS = [
    "lens.org",
    "uspto.gov",
    "epo.org",
    "wipo.int",
    "google.com",
    "googleapis.com",
    "patentimages.storage.googleapis.com",
]


def is_safe_url(url: str) -> bool:
    """Validate URL is an https link from a trusted patent image source."""
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    return any(domain in parsed.netloc for domain in _ALLOWED_DOMAINS)


class ImageTab(Static):
    """Image tab: inline rendering or external viewer with thumbnail strip."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_loaded = False
        self.current_record: PatentRecord | None = None
        self._current_fig_index = 0

    async def load_image(self, record: PatentRecord) -> None:
        self.current_record = record
        self._current_fig_index = 0
        self.update("Loading figures...")
        await asyncio.sleep(0.05)
        self._render_current()
        self.is_loaded = True

    def next_figure(self) -> None:
        """Advance to next figure (PRD key `n`)."""
        if self.current_record and self.current_record.image_urls:
            count = len(self.current_record.image_urls)
            self._current_fig_index = (self._current_fig_index + 1) % count
            self._render_current()

    def prev_figure(self) -> None:
        """Go to previous figure (PRD key `p` in image context)."""
        if self.current_record and self.current_record.image_urls:
            count = len(self.current_record.image_urls)
            self._current_fig_index = (self._current_fig_index - 1) % count
            self._render_current()

    def jump_to(self, index: int) -> None:
        """Jump to figure N (PRD key `1-9` in image context)."""
        if self.current_record and self.current_record.image_urls:
            count = len(self.current_record.image_urls)
            if 0 <= index < count:
                self._current_fig_index = index
                self._render_current()

    def open_external(self) -> None:
        """Open current figure in external viewer (PRD key `o`)."""
        if not self.current_record or not self.current_record.image_urls:
            self.update("ERR: No figures available.")
            return
        url = self.current_record.image_urls[self._current_fig_index]
        if not is_safe_url(url):
            self.update(f"ERR: Blocked unsafe or untrusted URL.\nURL: {escape(url)}")
            return
        try:
            subprocess.Popen(
                ["xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            self.update(f"ERR: Could not open external viewer: {escape(str(e))}")

    def _render_current(self) -> None:
        record = self.current_record
        if not record:
            self.update("No patent selected.")
            return

        urls = record.image_urls or []
        total = len(urls)

        if total == 0:
            protocol = detect_terminal_protocol()
            self.update(
                f"─── Figures ────────────────────────────────────\n"
                f"No figures available for this patent.\n\n"
                f"Terminal: {protocol.value}\n"
            )
            return

        idx = self._current_fig_index
        url = urls[idx]
        protocol = detect_terminal_protocol()

        # Thumbnail strip
        thumbs = []
        for i in range(total):
            if i == idx:
                thumbs.append(f"[{i+1}●]")
            else:
                thumbs.append(f"[{i+1} ]")
        thumb_strip = "  ".join(thumbs)

        from core.config import load_config
        config = load_config()

        if config.terminal_protocol == "none":
            body = "INFO: Figure rendering disabled (Text-only mode selected).\nAction: Press Enter on detection screen to change."
        elif protocol in (TerminalProtocol.KITTY, TerminalProtocol.ITERM2, TerminalProtocol.SIXEL):
            body = f"[INLINE {protocol.value.upper()} RENDER]\nURL: {escape(url)}"
        else:
            body = (
                f"ERR: Image rendering unsupported in current terminal.\n"
                f"Action: Open externally or switch to Kitty/iTerm2/WezTerm.\n"
                f"URL: {escape(url)}"
            )

        content = (
            f"─── Figures ────────────────────────────────────\n"
            f"FIGURE {idx + 1} OF {total}\n\n"
            f"{body}\n\n"
            f"{thumb_strip}\n\n"
            f"(n)ext  (p)rev  (o)pen external  (d)ownload figure"
        )
        self.update(content)

    def reset(self) -> None:
        self.is_loaded = False
        self.current_record = None
        self._current_fig_index = 0
        self.update("")
