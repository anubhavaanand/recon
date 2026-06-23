from textual.app import App, ComposeResult
from tui.screens import SearchScreen


class ReconApp(App):
    TITLE = "RECON"
    CSS_PATH = "styles.css"

    def on_mount(self) -> None:
        from core.config import load_config
        from tui.screens import SearchScreen, TerminalDetectionScreen

        config = load_config()
        if not config.terminal_detection_seen:
            self.push_screen(TerminalDetectionScreen())
        else:
            self.push_screen(SearchScreen())
