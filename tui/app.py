from textual.app import App

from tui.screens import SearchScreen


class ReconApp(App):
    TITLE = "RECON"
    CSS_PATH = "styles.css"

    def on_mount(self) -> None:
        from textual.scrollbar import ScrollBarRender
        # Replace fractional block elements with full solid blocks to prevent terminal rendering corruption
        ScrollBarRender.VERTICAL_BARS = ["█", "█", "█", "█", "█", "█", "█", " "]
        ScrollBarRender.HORIZONTAL_BARS = ["█", "█", "█", "█", "█", "█", "█", " "]

        # Light/dark auto-detection (Hermes design item #4).
        # COLORFGBG="fg;background" — background 0-6/8 implies a dark terminal.
        colorfgbg = __import__("os").environ.get("COLORFGBG", "")
        try:
            bg = int(colorfgbg.split(";")[-1])
            self.dark = bg < 7
        except (ValueError, IndexError):
            self.dark = True

        from core.config import load_config
        from tui.screens import TerminalDetectionScreen

        config = load_config()
        if not config.terminal_detection_seen:
            self.push_screen(TerminalDetectionScreen())
        else:
            self.push_screen(SearchScreen())

