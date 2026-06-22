from textual.app import App, ComposeResult
from tui.screens import SearchScreen

class ReconApp(App):
    TITLE = "RECON"
    CSS = """
    /* ── Root ── */
    Screen {
        background: #0d1117;
        color: #c9d1d9;
    }

    /* ── Status bar (top + bottom static) ── */
    #status_top {
        width: 100%;
        height: 1;
        background: #161b22;
        color: #58a6ff;
        padding: 0 1;
    }
    #status_bottom {
        width: 100%;
        height: 1;
        background: #161b22;
        color: #8b949e;
        padding: 0 1;
    }

    /* ── Search input ── */
    #search_input {
        width: 100%;
        height: 3;
        border: none;
        background: #161b22;
        color: #c9d1d9;
        border-bottom: solid #30363d;
    }
    #search_input:focus {
        border-bottom: solid #58a6ff;
    }

    /* ── Two-column layout ── */
    #main_horizontal {
        height: 1fr;
        width: 100%;
    }

    /* ── Results list ── */
    #result_list {
        width: 32;
        height: 100%;
        border-right: solid #30363d;
        background: #0d1117;
    }
    ResultListItem {
        height: 1;
        padding: 0 1;
        color: #8b949e;
    }
    ResultListItem:hover {
        background: #161b22;
        color: #c9d1d9;
    }
    ResultListItem.--highlight {
        background: #1f2937;
        color: #58a6ff;
    }

    /* ── Preview / detail column ── */
    #preview_column {
        width: 1fr;
        height: 100%;
        background: #0d1117;
    }

    /* ── Tab bar (custom, rule-based) ── */
    #tab_bar {
        width: 100%;
        height: 1;
        background: #161b22;
        color: #8b949e;
        padding: 0 1;
    }

    /* ── Tab content panes ── */
    #info_tab {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        color: #c9d1d9;
    }
    #claims_tab {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        color: #c9d1d9;
        display: none;
    }
    #image_tab {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        color: #c9d1d9;
        display: none;
    }
    .tab-active {
        display: block;
    }

    /* ── Help overlay ── */
    #help_overlay {
        width: 48;
        height: auto;
        background: #161b22;
        color: #c9d1d9;
        border: solid #30363d;
        offset: 34 2;
        padding: 0 1;
        layer: overlay;
    }
    #help_overlay.hidden {
        display: none;
    }

    /* ── Export format overlay ── */
    #export_overlay {
        width: 44;
        height: auto;
        background: #161b22;
        color: #c9d1d9;
        border: solid #30363d;
        offset: 38 5;
        padding: 0 1;
        layer: overlay;
    }
    #export_overlay.hidden {
        display: none;
    }

    /* ── Source filter overlay ── */
    #source_filter_overlay {
        width: 48;
        height: auto;
        background: #161b22;
        color: #c9d1d9;
        border: solid #30363d;
        offset: 34 2;
        padding: 0 1;
        layer: overlay;
    }
    #source_filter_overlay.hidden {
        display: none;
    }

    /* ── Citation tree (inline, toggled via hidden class) ── */
    #citation_tree {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        color: #c9d1d9;
        background: #0d1117;
    }
    #citation_tree.hidden {
        display: none;
    }

    /* ── Terminal detection screen ── */
    TerminalDetectionScreen {
        align: center middle;
        background: #0d1117;
    }
    #terminal_detection_content {
        width: 60;
        height: auto;
        border: solid #30363d;
        background: #161b22;
        padding: 1 2;
        color: #c9d1d9;
    }

    /* ── Reader/Detail/Citation screens ── */
    #reader_content {
        width: 100%;
        height: 1fr;
        padding: 1 4;
        overflow-y: auto;
        color: #c9d1d9;
    }
    #reader_status {
        width: 100%;
        height: 1;
        padding: 0 2;
        background: #161b22;
        color: #8b949e;
    }
    .reader-content {
        padding: 1 4;
        overflow-y: auto;
    }
    .reader-status {
        width: 100%;
        height: 1;
        padding: 0 2;
        background: #161b22;
        color: #8b949e;
    }
    """

    def on_mount(self) -> None:
        from core.config import load_config
        from tui.screens import SearchScreen, TerminalDetectionScreen

        config = load_config()
        if not config.terminal_detection_seen:
            self.push_screen(TerminalDetectionScreen())
        else:
            self.push_screen(SearchScreen())
