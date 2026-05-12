import os
import asyncio
import subprocess
from enum import Enum
from textual.widgets import Static
from core.models import PatentRecord

class TerminalProtocol(Enum):
    KITTY = "kitty"
    ITERM2 = "iterm2"
    SIXEL = "sixel"
    FALLBACK = "fallback"

def detect_terminal_protocol() -> TerminalProtocol:
    term = os.environ.get("TERM", "").lower()
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    kitty_window = os.environ.get("KITTY_WINDOW_ID", "")
    mlterm_flag = os.environ.get("MLTERM", "")

    # Kitty explicit detection
    if "kitty" in term or kitty_window:
        return TerminalProtocol.KITTY

    # iTerm detection
    if "iterm" in term_program or "iterm" in term:
        return TerminalProtocol.ITERM2

    # WezTerm and Ghostty advertise themselves via TERM_PROGRAM
    if "wezterm" in term_program or "ghostty" in term_program:
        return TerminalProtocol.SIXEL

    # MLTERM or TERM explicitly set to 'mlterm' indicate sixel support
    if mlterm_flag or term == "mlterm":
        return TerminalProtocol.SIXEL

    # Simple check for sixel present in TERM
    if "sixel" in term:
        return TerminalProtocol.SIXEL

    return TerminalProtocol.FALLBACK

class ImageTab(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_loaded = False
        self.current_record = None

    async def load_image(self, record: PatentRecord):
        self.current_record = record
        self.update("Loading image...")
        # Simulate network delay for fetching deep data
        await asyncio.sleep(0.1)
        
        if not record.image_urls:
            self.update("No images available.")
            self.is_loaded = True
            return
            
        protocol = detect_terminal_protocol()
        url = record.image_urls[0]
        
        if protocol == TerminalProtocol.FALLBACK:
            # Fallback to external viewer logic. We don't want modal dialogs, 
            # so we just print a dry actionable error/message
            self.update(f"ERR: Image rendering unsupported in current terminal.\nAction: Open externally or use Kitty/iTerm2.\nURL: {url}")
            # Simulate external opening
            try:
                # E.g. xdg-open on linux - launch external viewer non-blocking
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:
            self.update(f"Rendering image using {protocol.value} protocol...\nURL: {url}")
            
        self.is_loaded = True

    def reset(self):
        self.is_loaded = False
        self.current_record = None
        self.update("")
