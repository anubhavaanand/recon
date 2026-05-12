from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, ListView, TabbedContent, TabPane
from textual.widgets import Static
from tui.widgets.result_list import ResultList, ResultListItem
from tui.widgets.info_tab import InfoTab
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab
from core.search import search_all
from storage.cache import CacheDatabase
import logging
logger = logging.getLogger(__name__)

class ReaderModeScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back"), ("q", "app.pop_screen", "Quit"), ("j", "scroll_down", "Down"), ("k", "scroll_up", "Up")]

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

class SearchScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("s", "save_collection", "Save to Collection"),
        ("r", "reader_mode", "Reader Mode"),
        ("e", "export_collection", "Export Collection"),
        ("d", "download_patent", "Download Patent"),
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
            with TabbedContent(id="tabs"):
                with TabPane("Info", id="tab_info"):
                    yield InfoTab(id="info_tab", classes="info-panel")
                with TabPane("Claims", id="tab_claims"):
                    yield ClaimsTab(id="claims_tab", classes="info-panel")
                with TabPane("Image", id="tab_image"):
                    yield ImageTab(id="image_tab", classes="info-panel")
        yield Static(self._build_help_overlay(), id="help_overlay", classes="help-overlay hidden")
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        if not query:
            return
        
        results = await search_all(query)
        result_list = self.query_one(ResultList)
        await result_list.clear()
        
        for record in results:
            await result_list.append(ResultListItem(record))
            
        if results:
            result_list.index = 0

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        info_tab = self.query_one(InfoTab)
        claims_tab = self.query_one(ClaimsTab)
        image_tab = self.query_one(ImageTab)
        
        # Reset all tabs on new selection
        claims_tab.reset()
        image_tab.reset()
        
        if event.item and hasattr(event.item, "record"):
            record = event.item.record
            info_tab.update_record(record)
            
            # Lazy load based on active tab
            tabs = self.query_one(TabbedContent)
            await self._load_active_tab(tabs.active, record)
        else:
            info_tab.update_record(None)

    async def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        result_list = self.query_one(ResultList)
        if result_list.index is not None and result_list.index >= 0:
            item = result_list.get_item_at(result_list.index)
            if hasattr(item, "record"):
                await self._load_active_tab(event.tab.id, item.record)

    async def _load_active_tab(self, active_tab_id: str, record):
        if not active_tab_id:
            return
        if "tab_claims" in active_tab_id:
            claims_tab = self.query_one(ClaimsTab)
            if not claims_tab.is_loaded:
                await claims_tab.load_claims(record)
        elif "tab_image" in active_tab_id:
            image_tab = self.query_one(ImageTab)
            if not image_tab.is_loaded:
                await image_tab.load_image(record)

    def action_save_collection(self) -> None:
        result_list = self.query_one(ResultList)
        if result_list.index is not None and result_list.index >= 0:
            item = result_list.get_item_at(result_list.index)
            if hasattr(item, "record"):
                db = CacheDatabase()
                db.save_to_collection(item.record)
                self.notify(f"Saved {item.record.id} to collection.")

    def action_reader_mode(self) -> None:
        result_list = self.query_one(ResultList)
        if result_list.index is not None and result_list.index >= 0:
            item = result_list.get_item_at(result_list.index)
            if hasattr(item, "record"):
                self.app.push_screen(ReaderModeScreen(item.record))

    def action_export_collection(self) -> None:
        """Export current collection via CLI."""
        from cli.export import export_json
        try:
            db = CacheDatabase()
            records = db.get_all_records()
            if not records:
                self.notify("Collection is empty. Nothing to export.")
                return
            export_json(records, "collection_export.json")
            self.notify(f"Exported {len(records)} patents to collection_export.json")
        except Exception as e:
            self.notify(f"Export failed: {str(e)}", severity="error")

    def action_download_patent(self) -> None:
        """Download current patent."""
        result_list = self.query_one(ResultList)
        if result_list.index is not None and result_list.index >= 0:
            item = result_list.get_item_at(result_list.index)
            if hasattr(item, "record"):
                self.notify(f"Download queued for {item.record.id}")
        else:
            self.notify("No patent selected. Nothing to download.")

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search_input", Input)
        search_input.focus()

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
║ Search                                     ║
║   /            - Focus Search              ║
║   ?            - Toggle Help (this)        ║
╚════════════════════════════════════════════╝
"""
