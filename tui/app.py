from textual.app import App
from textual.theme import Theme

from tui.screens import SearchScreen


RECON_THEME = Theme(
    name="recon",
    primary="#7aa2f7",
    secondary="#bb9af7",
    accent="#7dcfff",
    foreground="#c0caf5",
    background="#16161e",
    surface="#1f2335",
    panel="#24283b",
    success="#9ece6a",
    warning="#e0af68",
    error="#f7768e",
    dark=True,
    variables={
        "block-cursor-background": "#7aa2f7",
        "input-selection-background": "#7aa2f7 35%",
        "footer-key-foreground": "#7dcfff",
    },
)


class ReconApp(App):
    TITLE = "RECON"
    CSS_PATH = "styles.css"

    def get_default_screen(self):
        # Engine-driven theming for every widget (footer keys,
        # scrollbars, focus rings, inputs, selections).
        return SearchScreen()

    def on_mount(self) -> None:
        self.register_theme(RECON_THEME)
        self.theme = "recon"

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

