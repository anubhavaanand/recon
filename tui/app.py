from textual.app import App, ComposeResult
from tui.screens import SearchScreen

class ReconApp(App):
    CSS = """
    #result_list {
        width: 30%;
        height: 100%;
        border-right: solid green;
    }
    #tabs {
        width: 70%;
        height: 100%;
    }
    .info-panel {
        padding: 1 2;
        width: 100%;
        height: 100%;
    }
    #reader_content {
        width: 100%;
        height: 1fr;
        padding: 2 4;
        overflow-y: auto;
    }
    #reader_status {
        width: 100%;
        height: auto;
        padding: 0 2;
        border-top: solid $accent;
        background: $boost;
    }
    .reader-content {
        padding: 2 4;
        overflow-y: auto;
    }
    .reader-status {
        width: 100%;
        height: auto;
        padding: 0 2;
        border-top: solid $accent;
        background: $boost;
    }
    #help_overlay {
        width: 50;
        height: auto;
        border: solid yellow;
        background: $surface;
        offset: 10 5;
        padding: 0 2;
    }
    #help_overlay.hidden {
        display: none;
    }
    """
    
    def on_mount(self) -> None:
        self.push_screen(SearchScreen())
