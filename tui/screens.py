from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.widgets import Header, Footer, Input, ListView, TabbedContent, TabPane
from textual.widgets import Static
from tui.widgets.result_list import ResultList, ResultListItem
from tui.widgets.info_tab import InfoTab
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab, detect_terminal_protocol, TerminalProtocol
from core.search import search_all
from storage.cache import CacheDatabase
import logging
logger = logging.getLogger(__name__)

class TerminalDetectionScreen(Screen):
    BINDINGS = [
        ("enter", "continue", "Continue"),
        ("q", "app.quit", "Quit")
    ]

    def compose(self) -> ComposeResult:
        protocol = detect_terminal_protocol()
        term = protocol.value
        supported = "✅ Supported" if protocol in [TerminalProtocol.KITTY, TerminalProtocol.ITERM2, TerminalProtocol.SIXEL] else "❌ Not supported"

        content = f"""
┌─ RECON ─────────────────────────────────────────────┐
│                                                       │
│  Terminal Detection                                   │
│                                                       │
│  Your terminal: {term:<37} │
│  Inline images: {supported:<37} │
│                                                       │
│  Options:                                             │
│  [Enter] Continue to Search                           │
│  [q]     Quit                                         │
│                                                       │
└───────────────────────────────────────────────────────┘
"""
        yield Static(content, id="terminal_detection_content")

    def action_continue(self) -> None:
        from core.config import load_config, save_config
        config = load_config()
        config.terminal_detection_seen = True
        save_config(config)
        self.app.switch_screen(SearchScreen())


class CitationGraphScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"), 
        ("q", "app.pop_screen", "Quit")
    ]

    def __init__(self, record, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self.citations = {"forward": [], "backward": []}
        self.loading = True

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Loading citations...", id="citation_graph", classes="reader-content")
            yield Static("Citation Graph | q: quit | Esc: back", id="graph_status", classes="reader-status")

    async def on_mount(self) -> None:
        from clients.patent_apis import LensClient
        if not self.record:
            return
            
        client = LensClient()
        self.citations = await client.fetch_citations(self.record.id)
        self.loading = False
        self.query_one("#citation_graph", Static).update(self._build_graph())

    def _build_graph(self) -> str:
        if not self.record:
            return "No patent selected."
        
        if self.loading:
            return "Loading citations..."
            
        forward = self.citations.get("forward", [])
        backward = self.citations.get("backward", [])
        
        lines = [f"# Citation Graph: {self.record.id}", "", f"Root: {self.record.id} ({self.record.assignee})", "│"]
        
        lines.append("├── Cited by (Forward Citations)")
        if not forward:
            lines.append("│   └── None found or Lens API key missing.")
        else:
            for i, c in enumerate(forward[:10]):
                prefix = "│   └──" if i == len(forward[:10]) - 1 else "│   ├──"
                title = c.get('title', '[?]')[:40] + "..." if len(c.get('title', '[?]')) > 40 else c.get('title', '[?]')
                lines.append(f"{prefix} {c.get('id', '[?]')} - \"{title}\"")
        
        lines.append("│")
        lines.append("└── Cites (Backward Citations)")
        if not backward:
            lines.append("    └── None found or Lens API key missing.")
        else:
            for i, c in enumerate(backward[:10]):
                prefix = "    └──" if i == len(backward[:10]) - 1 else "    ├──"
                title = c.get('title', '[?]')[:40] + "..." if len(c.get('title', '[?]')) > 40 else c.get('title', '[?]')
                lines.append(f"{prefix} {c.get('id', '[?]')} - \"{title}\"")

        return "\n".join(lines)

class ReaderModeScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"), 
        ("q", "app.pop_screen", "Quit"), 
        ("j", "scroll_down", "Down"), 
        ("k", "scroll_up", "Up"),
        ("t", "translate", "Translate")
    ]

    def __init__(self, record, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._build_content(), id="reader_content", classes="reader-content")
            yield Static("Reader Mode | q: quit | j/k: scroll", id="reader_status", classes="reader-status")

    def _build_content(self) -> str:
        if not self.record:
            return "No patent selected."
        
        claims_text = "\n\n".join(self.record.claims) if self.record.claims else "No claims available."
        
        return f"""
# {self.record.title}
**ID**: {self.record.id} | **Assignee**: {self.record.assignee} | **Filed**: {self.record.dates.get('filed', '[?]')}

## Abstract
{self.record.abstract}

---
## Claims
{claims_text}
"""

    def action_scroll_down(self) -> None:
        content = self.query_one("#reader_content", Static)
        if hasattr(content, 'scroll_down'):
            content.scroll_down()

    def action_scroll_up(self) -> None:
        content = self.query_one("#reader_content", Static)
        if hasattr(content, 'scroll_up'):
            content.scroll_up()

    async def action_translate(self) -> None:
        from core.translation import translate_text
        if not self.record:
            return
            
        self.notify("Translating document...")
        
        # Translate abstract
        if not "[t]ranslated" in self.record.abstract:
            self.record.abstract = await translate_text(self.record.abstract) + "\n\n[t]ranslated from original by DeepSeek"
        
        # Translate claims
        if self.record.claims:
            translated_claims = []
            for claim in self.record.claims:
                translated_claims.append(await translate_text(claim))
            self.record.claims = translated_claims
            
        content = self.query_one("#reader_content", Static)
        content.update(self._build_content())
        self.notify("Translation complete.")

class SearchScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("s", "save_collection", "Save to Collection"),
        ("r", "reader_mode", "Reader Mode"),
        ("e", "export_collection", "Export Collection"),
        ("d", "download_patent", "Download Patent"),
        ("t", "translate", "Translate"),
        ("c", "show_citation_graph", "Citation Graph"),
        ("/", "focus_search", "Focus Search"),
        ("?", "show_help", "Help")
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_help_overlay = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search patents...", id="search_input")
        with Horizontal():
            yield ResultList(id="result_list")
            with Vertical(id="details_column"):
                yield InfoTab(id="info_tab", classes="info-panel")
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        if not query:
            return
        
        self.notify(f"Searching for: {query}")
        results = await search_all(query)
        result_list = self.query_one(ResultList)
        result_list.clear()
        
        for record in results:
            result_list.mount(ResultListItem(record))
            
        if results:
            # Manually trigger first item preview
            result_list.index = 0
            first_record = results[0]
            
            info_tab = self.query_one(InfoTab)
            info_tab.update_record(first_record)

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        try:
            info_tab = self.query_one(InfoTab)
            if event.item and hasattr(event.item, "record"):
                record = event.item.record
                self.notify(f"Loading: {record.id}")
                info_tab.update_record(record)
            else:
                info_tab.update_record(None)
        except Exception as e:
            self.notify(f"ERR: {str(e)}", severity="error")

    async def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        try:
            result_list = self.query_one(ResultList)
            item = result_list.highlighted_child
            
            tab_id = event.tab.id
            logger.debug(f"Tab activated: {tab_id} (type: {type(tab_id)})")
            self.notify(f"📑 Tab: {tab_id}")
            
            if item is not None and hasattr(item, "record"):
                logger.debug(f"Loading tab content for {item.record.id}")
                await self._load_active_tab(tab_id, item.record)
            else:
                logger.debug(f"No item selected when tab activated")
        except Exception as e:
            logger.error(f"Error in on_tabbed_content_tab_activated: {e}", exc_info=True)
            self.notify(f"❌ Tab Error: {str(e)}", severity="error")

    async def _load_active_tab(self, active_tab_id: str, record):
        logger.debug(f"_load_active_tab called with: {active_tab_id!r} (type: {type(active_tab_id).__name__})")
        
        if not active_tab_id:
            logger.debug(f"No active_tab_id provided")
            return
        
        # Strip Textual's automatic "--content-tab-" prefix if present
        tab_id_str = str(active_tab_id).lower()
        if tab_id_str.startswith("--content-tab-"):
            tab_id_str = tab_id_str.replace("--content-tab-", "")
            logger.debug(f"✓ Stripped tab ID prefix: {active_tab_id!r} → {tab_id_str!r}")
        
        try:
            # Match normalized tab ID
            if "info" in tab_id_str or tab_id_str == "tab_info":
                logger.debug(f"Info tab active - already loaded in on_list_view_highlighted")
            elif "claims" in tab_id_str or tab_id_str == "tab_claims":
                logger.debug(f"Loading claims...")
                claims_tab = self.query_one(ClaimsTab)
                if not claims_tab.is_loaded:
                    logger.debug(f"Calling claims_tab.load_claims()...")
                    await claims_tab.load_claims(record)
                    logger.debug(f"✓ Claims loaded")
                else:
                    logger.debug(f"Claims already loaded")
            elif "image" in tab_id_str or tab_id_str == "tab_image":
                logger.debug(f"Loading image...")
                image_tab = self.query_one(ImageTab)
                if not image_tab.is_loaded:
                    logger.debug(f"Calling image_tab.load_image()...")
                    await image_tab.load_image(record)
                    logger.debug(f"✓ Image loaded")
                else:
                    logger.debug(f"Image already loaded")
            else:
                logger.debug(f"⚠ Unknown tab ID format after normalization: {tab_id_str!r}")
        except Exception as e:
            logger.error(f"Error in _load_active_tab: {e}", exc_info=True)

    def action_save_collection(self) -> None:
        result_list = self.query_one(ResultList)
        item = result_list.highlighted_child
        if item is not None and hasattr(item, "record"):
            db = CacheDatabase()
            db.save_to_collection(item.record)
            self.notify(f"Saved {item.record.id} to collection.")

    def action_reader_mode(self) -> None:
        result_list = self.query_one(ResultList)
        item = result_list.highlighted_child
        if item is not None and hasattr(item, "record"):
            self.app.push_screen(ReaderModeScreen(item.record))

    def action_show_citation_graph(self) -> None:
        result_list = self.query_one(ResultList)
        item = result_list.highlighted_child
        if item is not None and hasattr(item, "record"):
            self.app.push_screen(CitationGraphScreen(item.record))

    def action_export_collection(self) -> None:
        """Export current collection via CLI."""
        from cli.export import export_records
        try:
            db = CacheDatabase()
            records = db.get_collection()
            if not records:
                self.notify("Collection is empty. Nothing to export.")
                return
            export_records(records, "json", "collection_export.json")
            self.notify(f"Exported {len(records)} patents to collection_export.json")
        except Exception as e:
            self.notify(f"Export failed: {str(e)}", severity="error")

    def action_download_patent(self) -> None:
        """Download current patent."""
        result_list = self.query_one(ResultList)
        item = result_list.highlighted_child
        if item is not None and hasattr(item, "record"):
            self.notify(f"Download queued for {item.record.id}")
        else:
            self.notify("No patent selected. Nothing to download.")

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search_input", Input)
        search_input.focus()

    async def action_translate(self) -> None:
        from core.translation import translate_text
        result_list = self.query_one(ResultList)
        item = result_list.highlighted_child
        if item is not None and hasattr(item, "record"):
            record = item.record
            self.notify(f"Translating {record.id}...")
            
            # Translate abstract
            if not "[t]ranslated" in record.abstract:
                record.abstract = await translate_text(record.abstract) + "\n\n[t]ranslated from original by DeepSeek"
            
            # Translate title
            record.title = await translate_text(record.title)
            
            # Translate claims if any
            if record.claims:
                translated_claims = []
                for claim in record.claims:
                    translated_claims.append(await translate_text(claim))
                record.claims = translated_claims
            
            # Refresh UI
            info_tab = self.query_one(InfoTab)
            info_tab.update_record(record)
            
            claims_tab = self.query_one(ClaimsTab)
            if claims_tab.is_loaded:
                await claims_tab.load_claims(record)
            
            self.notify(f"Translation complete for {record.id}")

    def action_show_help(self) -> None:
        """Toggle help overlay."""
        help_overlay = self.query_one("#help_overlay", Static)
        if "hidden" in help_overlay.classes:
            help_overlay.remove_class("hidden")
            self.show_help_overlay = True
        else:
            help_overlay.add_class("hidden")
            self.show_help_overlay = False

    def _build_help_overlay(self) -> str:
        return """
╔════════════════════════════════════════════╗
║           KEYBOARD SHORTCUTS               ║
╠════════════════════════════════════════════╣
║ Navigation                                 ║
║   ↑/↓ or j/k  - Navigate results          ║
║   r            - Open selected in Reader   ║
║   q or Esc     - Quit/Back                 ║
║                                            ║
║ Collection                                 ║
║   s            - Save to Collection        ║
║   e            - Export Collection         ║
║   d            - Download Patent           ║
║                                            ║
║ Search & Analysis                          ║
║   /            - Focus Search              ║
║   t            - Translate Patent          ║
║   c            - Citation Graph            ║
║   ?            - Toggle Help (this)        ║
╚════════════════════════════════════════════╝
"""
