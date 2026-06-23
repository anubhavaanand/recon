from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, ListView, Static
from textual import work
from textual.events import Resize
from textual.reactive import reactive


from rich.markup import escape

from tui.widgets.result_list import ResultList, ResultListItem
from tui.widgets.info_tab import InfoTab
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab, detect_terminal_protocol, TerminalProtocol
from tui.widgets.citation_tree import CitationTree
from tui.widgets.command_palette import CommandPalette
from core.search import search_all, ALL_SOURCES, SOURCE_REGISTRY
from core.intelligence import SynthesisEngine
from storage.cache import CacheDatabase


# ══════════════════════════════════════════════
# TERMINAL DETECTION SCREEN  (PRD §3.6)
# ══════════════════════════════════════════════
class TerminalDetectionScreen(Screen):
    BINDINGS = [
        ("enter", "confirm", "Continue"),
        ("q",     "app.quit", "Quit"),
        ("1",     "select_option('external')", "External viewer"),
        ("2",     "select_option('switch')",   "Switch terminal"),
        ("3",     "select_option('none')",     "Text-only mode"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected = "external"

    def compose(self) -> ComposeResult:
        yield Static(self._build_content(), id="terminal_detection_content")

    def _build_content(self) -> str:
        protocol = detect_terminal_protocol()
        term = protocol.value
        supported = (
            "✅ Supported" if protocol != TerminalProtocol.FALLBACK
            else "❌ Not supported"
        )
        
        def mark(opt):
            return "●" if self._selected == opt else " "

        content = (
            f"┌─ RECON ─────────────────────────────────────────────┐\n"
            f"│                                                       │\n"
            f"│  Terminal Detection                                   │\n"
            f"│                                                       │\n"
            f"│  Your terminal: {term:<37}│\n"
            f"│  Inline images: {supported:<37}│\n"
            f"│                                                       │\n"
            f"│  Options (Press 1, 2, or 3 to select):                │\n"
            f"│                                                       │\n"
            f"│  [1][{mark('external')}] Use external viewer (recommended)            │\n"
            f"│         Press o to open figure in Preview/feh         │\n"
            f"│                                                       │\n"
            f"│  [2][{mark('switch')}] Switch to supported terminal                  │\n"
            f"│         Kitty, iTerm2, WezTerm, or Ghostty            │\n"
            f"│                                                       │\n"
            f"│  [3][{mark('none')}] Continue without images                       │\n"
            f"│         Text-only mode, figure captions only          │\n"
            f"│                                                       │\n"
            f"│  [Enter] Confirm  [q] Quit                            │\n"
            f"│                                                       │\n"
            f"└───────────────────────────────────────────────────────┘"
        )
        return content

    def action_select_option(self, option: str) -> None:
        self._selected = option
        self.query_one("#terminal_detection_content", Static).update(self._build_content())

    def action_confirm(self) -> None:
        from core.config import load_config, save_config
        config = load_config()
        config.terminal_detection_seen = True
        config.terminal_protocol = self._selected
        save_config(config)
        self.app.switch_screen(SearchScreen())


# ══════════════════════════════════════════════
# CITATION GRAPH SCREEN  (PRD §4 — `c` key)
# ══════════════════════════════════════════════
class CitationGraphScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q",      "app.pop_screen", "Quit"),
    ]

    def __init__(self, record, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self.citations: dict = {"forward": [], "backward": []}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Loading citations...", id="citation_graph", classes="reader-content")
            yield Static(
                f"Citation Graph: {escape(self.record.id)} │ Esc: back",
                id="graph_status", classes="reader-status"
            )

    async def on_mount(self) -> None:
        from clients.patent_apis import LensClient
        if not self.record:
            return
        client = LensClient()
        self.citations = await client.fetch_citations(self.record.id)
        self.query_one("#citation_graph", Static).update(self._build_graph())

    def _build_graph(self) -> str:
        if not self.record:
            return "No patent selected."
        forward  = self.citations.get("forward", [])
        backward = self.citations.get("backward", [])
        lines = [
            f"# Citation Graph: {escape(self.record.id)}",
            f"Root: {escape(self.record.id)} ({escape(self.record.assignee)})",
            "│",
            "├── Cited by (Forward Citations)",
        ]
        if not forward:
            lines.append("│   └── None found (Lens API key missing?)")
        else:
            for i, c in enumerate(forward[:10]):
                pfx = "│   └──" if i == len(forward[:10]) - 1 else "│   ├──"
                t = escape(c.get("title", "[?]")[:50])
                lines.append(f"{pfx} {escape(c.get('id', '[?]'))} — \"{t}\"")
        lines += ["│", "└── Cites (Backward Citations)"]
        if not backward:
            lines.append("    └── None found.")
        else:
            for i, c in enumerate(backward[:10]):
                pfx = "    └──" if i == len(backward[:10]) - 1 else "    ├──"
                t = escape(c.get("title", "[?]")[:50])
                lines.append(f"{pfx} {escape(c.get('id', '[?]'))} — \"{t}\"")
        return "\n".join(lines)


# ══════════════════════════════════════════════
# FAMILY TREE SCREEN  (PRD §4 — `f` key)
# ══════════════════════════════════════════════
class FamilyTreeScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q",      "app.pop_screen", "Quit"),
    ]

    def __init__(self, record, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._build_tree(), id="family_tree_content", classes="reader-content")
            yield Static(
                f"Family Tree: {escape(self.record.id)} │ Esc: back",
                id="family_tree_status", classes="reader-status"
            )

    def _build_tree(self) -> str:
        if not self.record:
            return "No patent selected."
        
        # Simulate family members based on family_id
        fid = self.record.family_id or "F-UNKNOWN"
        lines = [
            f"# Family Tree: {escape(fid)}",
            "│",
            f"├── {escape(self.record.id)} (Root - {escape(self.record.assignee)})",
        ]
        
        # Add mock family members
        mock_members = [
            ("CN2023001", "Active"),
            ("EP2023002", "Pending"),
            ("JP2023003", "Active"),
            ("KR2023004", "Expired"),
        ]
        for i, (mid, status) in enumerate(mock_members):
            pfx = "└──" if i == len(mock_members) - 1 else "├──"
            lines.append(f"{pfx} {escape(mid)} [{status}]")
            
        return "\n".join(lines)


# ══════════════════════════════════════════════
# SYNTHESIS SCREEN  (PRD §5)
# ══════════════════════════════════════════════
class SynthesisScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q",      "app.pop_screen", "Quit"),
    ]

    def __init__(self, records, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = records

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Generating synthesis summary via Ollama...", id="synthesis_content", classes="reader-content")
            yield Static(
                f"Intelligence Synthesis │ {len(self.records)} patents │ Esc: back",
                id="synthesis_status", classes="reader-status"
            )

    async def on_mount(self) -> None:
        engine = SynthesisEngine()
        summary = await engine.summarize_results(self.records)
        self.query_one("#synthesis_content", Static).update(summary)


# ══════════════════════════════════════════════
# READER MODE SCREEN  (PRD §3.3)
# ══════════════════════════════════════════════
class ReaderModeScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q",      "app.pop_screen", "Quit"),
        ("j",      "scroll_down",    "Down"),
        ("k",      "scroll_up",      "Up"),
        ("t",      "translate",      "Translate"),
    ]

    def __init__(self, record, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self._original_abstract: str | None = None

    def compose(self) -> ComposeResult:
        # PRD §3.3: No Header, No Footer — full width content + minimal status line
        with Vertical():
            yield Static(self._build_content(), id="reader_content", classes="reader-content")
            yield Static(self._status_line(), id="reader_status", classes="reader-status")

    async def on_mount(self) -> None:
        if not self.record.claims or self.record.claims == ["[?]"]:
            self.query_one("#reader_status", Static).update(self._status_line() + " │ Fetching full text...")
            from core.search import search_all
            try:
                # Use Google Patents scraper to fetch full text specifically for this ID
                results = await search_all(self.record.id, sources=["google"])
                if results:
                    best = results[0]
                    if best.abstract and best.abstract != "[?]":
                        self.record.abstract = best.abstract
                    if best.claims and best.claims != ["[?]"]:
                        self.record.claims = best.claims
                    self.query_one("#reader_content", Static).update(self._build_content())
            except Exception:
                pass
            self.query_one("#reader_status", Static).update(self._status_line())

    def _status_line(self) -> str:
        total_claims = len(self.record.claims) if self.record and self.record.claims else 0
        return f"Reader Mode │ {total_claims} claims │ (↑↓) scroll  (c)laims  (d)ownload  (s)ave  (Esc) back"

    def _build_content(self) -> str:
        if not self.record:
            return "No patent selected."
        r = self.record
        claims_text = ""
        for i, claim in enumerate(r.claims or [], 1):
            is_dep = "of claim" in claim.lower()
            label = "Dependent" if is_dep else "Independent"
            claims_text += f"\nCLAIM {i} ({label})\n{'─' * 48}\n{escape(claim.strip())}\n"

        return (
            f"RECON ── READER ── {escape(r.id)}\n"
            f"{escape(r.assignee)} │ {len(r.claims or [])} claims\n"
            f"\n"
            f"ABSTRACT\n"
            f"{'─' * 48}\n"
            f"{escape(r.abstract)}\n"
            f"\n"
            f"{'─' * 48}\n"
            f"{claims_text}"
        )

    def action_scroll_down(self) -> None:
        self.query_one("#reader_content", Static).scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#reader_content", Static).scroll_up(animate=False)

    async def action_translate(self) -> None:
        if not self.record:
            return
        from core.translation import translate_text

        if self._original_abstract is not None:
            # Revert to original
            self.record.abstract = self._original_abstract
            self._original_abstract = None
            self.query_one("#reader_content", Static).update(self._build_content())
            self.app.notify("Reverted to original.")
            return

        self.app.notify("Translating...")
        self._original_abstract = self.record.abstract
        translated = await translate_text(self.record.abstract)
        if translated != self._original_abstract and not translated.startswith("ERR:"):
            self.record.abstract = translated
            self.query_one("#reader_content", Static).update(self._build_content())
            self.app.notify("Translation complete.")
        else:
            self._original_abstract = None
            if translated.startswith("ERR:"):
                self.app.notify(translated, severity="error")
            else:
                self.app.notify("Text already in English — no translation needed.")
        self.app.notify("Translation complete.")


# ══════════════════════════════════════════════
# DETAIL VIEW SCREEN  (PRD §3.2)
# ══════════════════════════════════════════════
class DetailScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("s",      "save",           "Save"),
        ("d",      "download",       "Download"),
        ("e",      "export",         "Export"),
        ("o",      "open_external",  "Open External"),
        ("r",      "reader_mode",    "Reader Mode"),
        ("c",      "toggle_citations", "Citations"),
        ("f",      "family_tree",    "Family Tree"),
        ("t",      "translate",      "Translate"),
        ("j",      "scroll_down",    "Down"),
        ("k",      "scroll_up",      "Up"),
    ]

    _show_citations: reactive[bool] = reactive(False)
    _show_translation: reactive[bool] = reactive(False)

    def __init__(self, record, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self._original_abstract: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._build_content(), id="detail_content", classes="reader-content")
            yield CitationTree(
                "Press [c] to load citation graph...",
                id="citation_tree",
                classes="hidden",
            )
            yield Static(self._status_line(), id="detail_status", classes="reader-status")

    def _status_line(self) -> str:
        citation_hint = "hide cit." if self._show_citations else "citations"
        translate_hint = "orig." if self._show_translation else "translate"
        return (
            f"Esc: back  (s)ave  (d)ownload  (e)xport  (o)pen  "
            f"(r)eader  (c){citation_hint}  (t){translate_hint}  "
            f"(f)amily  (j/k) scroll"
        )

    def watch__show_citations(self, showing: bool) -> None:
        """Reactively toggle the citation tree visibility."""
        tree = self.query_one("#citation_tree", CitationTree)
        if showing:
            tree.remove_class("hidden")
        else:
            tree.add_class("hidden")
        self.query_one("#detail_status", Static).update(self._status_line())

    def _build_content(self) -> str:
        if not self.record:
            return "No patent selected."
        r = self.record
        from tui.widgets.info_tab import _render_score_bar, _render_status_pill, _render_signal_dots
        from core.scoring import calculate_signal_score
        from core.arbitrage import calculate_arbitrage_status, render_arbitrage_table

        import textwrap
        score = calculate_signal_score(r.cross_references)
        status_pill = _render_status_pill(r.status)
        score_bar   = _render_score_bar(score)
        dots        = _render_signal_dots(r.cross_references) if r.cross_references else "No signals."

        claims_preview = ""
        for i, claim in enumerate((r.claims or [])[:3], 1):
            claim_text = escape(claim[:80].strip())
            claims_preview += textwrap.fill(f"{i}. {claim_text}...", width=56, break_long_words=True) + "\n"
        if not claims_preview:
            claims_preview = "No claims available.\n"

        arb_status = calculate_arbitrage_status(r)
        arb_table = render_arbitrage_table(arb_status)

        wrapped_abstract = textwrap.fill(r.abstract, width=56, break_long_words=True)

        return (
            f"RECON ── FULL DETAIL ── {escape(r.id)}\n"
            f"{escape(r.assignee)} │ {status_pill} │ Filed: {escape(r.dates.get('filed','[?]'))}\n"
            f"{'─' * 56}\n\n"
            f"ABSTRACT\n"
            f"{'─' * 56}\n"
            f"{escape(wrapped_abstract)}\n\n"
            f"CLAIMS\n"
            f"{'─' * 56}\n"
            f"{claims_preview}"
            f"  ... [r]eader for full text\n\n"
            f"INTELLIGENCE\n"
            f"{'─' * 56}\n"
            f"Score: {score_bar}\n"
            f"{dots}\n\n"
            f"ARBITRAGE\n"
            f"{'─' * 56}\n"
            f"{arb_table}\n"
        )

    def action_save(self) -> None:
        db = CacheDatabase()
        db.save_to_collection(self.record)
        self.app.notify(f"Saved {self.record.id} to collection.")

    def action_download(self) -> None:
        self.app.notify(f"Download queued for {self.record.id}.")

    def action_export(self) -> None:
        self.app.notify("Use 'recon export' from CLI to export collection.")

    def action_open_external(self) -> None:
        if self.record.image_urls:
            from tui.widgets.image_tab import is_safe_url
            import subprocess
            url = self.record.image_urls[0]
            if is_safe_url(url):
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.app.notify("ERR: Blocked unsafe URL.")
        else:
            self.app.notify("No figures available.")

    def action_reader_mode(self) -> None:
        self.app.push_screen(ReaderModeScreen(self.record))

    async def action_toggle_citations(self) -> None:
        """Toggle the inline citation tree widget."""
        self._show_citations = not self._show_citations
        if self._show_citations:
            self.app.notify("Loading citation graph...")
            try:
                from core.citations import fetch_citations
                graph = await fetch_citations(
                    self.record.id, self.record.assignee or ""
                )
                self.query_one("#citation_tree", CitationTree).render_graph(graph)
                self.app.notify(f"Citations: {len(graph.backward)} back, {len(graph.forward)} fwd")
            except Exception as e:
                self.app.notify(f"ERR: Citation fetch failed: {e}", severity="error")
                self._show_citations = False

    def action_family_tree(self) -> None:
        self.app.push_screen(FamilyTreeScreen(self.record))

    def action_scroll_down(self) -> None:
        target = self.query_one("#citation_tree", CitationTree) if self._show_citations else self.query_one("#detail_content", Static)
        target.scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        target = self.query_one("#citation_tree", CitationTree) if self._show_citations else self.query_one("#detail_content", Static)
        target.scroll_up(animate=False)

    def watch__show_translation(self, showing: bool) -> None:
        """Reactively toggle between translated and original abstract."""
        if not self.record:
            return
        if showing:
            # Save original and translate
            self.app.notify("Translating...")
            self.call_after_refresh(self._do_translate)
        else:
            # Restore original
            if self._original_abstract is not None:
                self.record.abstract = self._original_abstract
                self._original_abstract = None
                self.query_one("#detail_content", Static).update(self._build_content())
            self.query_one("#detail_status", Static).update(self._status_line())

    async def _do_translate(self) -> None:
        if not self.record:
            return
        self._original_abstract = self.record.abstract
        translated = await translate_text(self.record.abstract)
        if translated != self._original_abstract and not translated.startswith("ERR:"):
            self.record.abstract = translated
            self.query_one("#detail_content", Static).update(self._build_content())
            self.app.notify("Translation complete.")
        else:
            self._show_translation = False
            if translated.startswith("ERR:"):
                self.app.notify(translated, severity="error")
            else:
                self.app.notify("Text already in English — no translation needed.")
        self.query_one("#detail_status", Static).update(self._status_line())

    async def action_translate(self) -> None:
        if not self.record:
            self.app.notify("No patent selected.")
            return
        self._show_translation = not self._show_translation
        self.app.notify("Translation complete.")


# ══════════════════════════════════════════════
# SEARCH + LIVE PREVIEW SCREEN  (PRD §3.1)
# ══════════════════════════════════════════════
_HELP_TEXT = """\
┌─ Help Overlay ─────────────────────────────┐
│                                            │
│  NAVIGATION                                │
│  ↑↓ j/k   Navigate results                │
│  g/G      Jump to top/bottom of list       │
│  Enter     Open detail view                │
│  h/l ←/→  Switch preview tab              │
│  1-9       Quick-open result N             │
│                                            │
│  ACTIONS                                   │
│  s         Save to collection              │
│  e         Export collection               │
│  S         Source filter                   │
│  d         Download patent                 │
│  r         Reader mode                     │
│  c         Citation graph                  │
│  t         Translate                       │
│  p         Toggle three-pane               │
│  m         Synthesis mode                  │
│  a         Assignee portfolio view         │
│                                            │
│  SEARCH                                    │
│  /         Focus search input              │
│  ?         Toggle this help                │
│  q         Dismiss overlay / Quit          │
│  Esc       Back                            │
│                                            │
│  [?] Close  [Esc] Dismiss                  │
└────────────────────────────────────────────┘"""

_ASSIGNEE_HELP = """\
┌─ Assignee Portfolio View ───────────────────┐
│                                              │
│  Portfolios with active patents in results:  │
│  (select to filter by assignee)              │
│                                              │
│  [a] toggle   [Esc] dismiss   [q] dismiss    │
└──────────────────────────────────────────────┘"""


def _get_source_from_id(patent_id: str) -> str:
    """Infer source prefix from patent ID."""
    if not patent_id:
        return "UNKNOWN"
    prefix = patent_id[:2].upper()
    mapping = {"US": "USPTO", "EP": "EPO", "WO": "WIPO", "JP": "JPO", "CN": "CNIPA"}
    return mapping.get(prefix, "OTHER")


_TABS = ["info", "claims", "image"]


class SearchScreen(Screen):
    """Main Search + Live Preview screen — PRD §3.1."""

    BINDINGS = [
        ("escape",     "app.pop_screen",        "Back"),
        ("enter",      "open_detail",           "Detail"),
        ("s",          "save_collection",        "Save"),
        ("r",          "reader_mode",           "Reader"),
        ("e",          "export_collection",     "Export"),
        ("d",          "download_patent",       "Download"),
        ("t",          "translate",             "Translate"),
        ("c",          "show_citation_graph",   "Citations"),
        ("/",          "focus_search",          "Search"),
        ("?",          "toggle_help",           "Help"),
        ("S",          "toggle_source_filter",  "Source Filter"),
        ("h",          "prev_tab",              "Prev Tab"),
        ("l",          "next_tab",              "Next Tab"),
        ("left",       "prev_tab",              "Prev Tab"),
        ("right",      "next_tab",              "Next Tab"),
        ("i",          "toggle_independent",    "Indep. Claims"),
        ("n",          "next_figure",           "Next Figure"),
        ("p",          "prev_figure",           "Prev Figure"),
        ("m",          "toggle_synthesis",      "Synthesis Mode"),
        ("1",          "quick_open('1')",       "Open 1"),
        ("2",          "quick_open('2')",       "Open 2"),
        ("3",          "quick_open('3')",       "Open 3"),
        ("4",          "quick_open('4')",       "Open 4"),
        ("5",          "quick_open('5')",       "Open 5"),
        ("6",          "quick_open('6')",       "Open 6"),
        ("7",          "quick_open('7')",       "Open 7"),
        ("8",          "quick_open('8')",       "Open 8"),
        ("9",          "quick_open('9')",       "Open 9"),
        ("g",          "jump_to_top",           "Top"),
        ("G",          "jump_to_bottom",        "Bottom"),
        ("a",          "toggle_assignee_view",  "Assignee Portfolio"),
        ("w",          "toggle_sort",           "Sort & Weights"),
        ("x",          "toggle_semantic",       "Semantic Search"),
        ("q",          "dismiss_or_quit",       "Quit"),
    ]

    _active_tab: reactive[str] = reactive("info")
    _synthesis_mode: reactive[bool] = reactive(False)

    EXPORT_FORMATS = ["json", "csv", "bibtex", "markdown", "pdf"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._results: list = []
        self._show_help = False
        self._show_export = False
        self._export_selected = 0
        self._show_source_filter = False
        self._source_filter_selected = 0
        self._active_sources: set[str] = set(ALL_SOURCES)
        self._search_history: list[dict] = []
        self._search_history_index = -1
        self._show_assignee_view = False
        self._assignee_portfolios: dict[str, list] = {}
        self._input_error = False
        self._show_sort = False
        self._sort_selected = 0
        self._sort_mode = "relevance"
        self._semantic_enabled = False
        self._awaiting_nomic_consent = False

    def compose(self) -> ComposeResult:
        # Top status bar
        yield Static("RECON  ─────────────────────────────────────────", id="status_top")
        # Search input
        yield Input(placeholder='Search patents... ("sulfide electrolyte solid state battery")', id="search_input")
        # Command palette (hidden by default, shown when typing /)
        yield CommandPalette("", id="command_palette", classes="hidden")
        # Main two-column layout
        with Horizontal(id="main_horizontal"):
            yield ResultList(id="result_list")
            with Vertical(id="preview_column"):
                # Custom tab bar (rule-based, not TabbedContent widget)
                yield Static(self._render_tab_bar(), id="tab_bar")
                yield InfoTab(id="info_tab")
                yield ClaimsTab(id="claims_tab")
                yield ImageTab(id="image_tab")
        # Help overlay (hidden by default)
        yield Static(_HELP_TEXT, id="help_overlay", classes="hidden")
        # Export format selector overlay (hidden by default)
        yield Static("", id="export_overlay", classes="hidden")
        # Source filter overlay (hidden by default)
        yield Static("", id="source_filter_overlay", classes="hidden")
        # Sort overlay (hidden by default)
        yield Static("", id="sort_overlay", classes="hidden")
        # Nomic consent overlay (hidden by default)
        yield Static("", id="nomic_consent_overlay", classes="hidden")
        # Assignee Portfolio View overlay (hidden by default)
        yield Static("", id="assignee_overlay", classes="hidden")
        # Bottom status bar
        yield Static(
            "↑↓ nav  Enter:detail  /:cmds  s:save  e:export  a:assignee  w:sort  x:semantic  ?:help  q:quit",
            id="status_bottom"
        )

    def _render_tab_bar(self) -> str:
        tabs = {"info": "Info", "claims": "Claims", "image": "Image"}
        parts = []
        for key, label in tabs.items():
            if key == self._active_tab:
                parts.append(f"<{label}>")
            else:
                parts.append(f" {label} ")
        return "  ".join(parts) + "  ─────────────────────────────────"

    def _refresh_tab_bar(self) -> None:
        try:
            self.query_one("#tab_bar", Static).update(self._render_tab_bar())
        except Exception:
            pass

    def _set_active_tab(self, tab: str) -> None:
        """Show the active tab widget, hide others."""
        self._active_tab = tab
        self._refresh_tab_bar()
        for t in _TABS:
            try:
                widget_id = f"#{t}_tab"
                w = self.query_one(widget_id, Static)
                if t == tab:
                    w.add_class("tab-active")
                    w.remove_class("hidden") if "hidden" in w.classes else None
                    # Make visible via display
                    w.styles.display = "block"
                else:
                    w.styles.display = "none"
            except Exception:
                pass

    def on_key(self, event) -> None:
        # Nomic consent response takes top priority
        if getattr(self, "_awaiting_nomic_consent", False):
            from core.config import load_config, save_config
            key = event.key
            overlay = self.query_one("#nomic_consent_overlay", Static)
            event.stop()
            event.prevent_default()
            self._awaiting_nomic_consent = False
            overlay.add_class("hidden")
            overlay.update("")
            if key.lower() == "y":
                cfg = load_config()
                self.app.notify("Downloading nomic-embed-text (270MB)... This may take a few minutes.")
                self._do_pull_nomic(cfg)
            else:
                cfg = load_config()
                cfg.nomic_consent_given = True
                save_config(cfg)
                self.app.notify("Semantic Search disabled.")
            return

        # Command palette takes priority
        palette = self.query_one("#command_palette", CommandPalette)
        if palette.is_active:
            handled = self._on_key_command_palette(event)
            if handled:
                event.stop()
                return

        # Handle q to dismiss any active overlay
        if event.key == "q":
            if self._dismiss_active_overlay():
                event.stop()
                return

        # Handle up arrow on search input for history cycling
        if event.key == "up" and self.query_one("#search_input", Input).has_focus:
            self._cycle_search_history(-1)
            event.stop()
            return

        if self._show_source_filter:
            handled = self._on_key_source_filter(event)
            if handled:
                event.stop()
                return

        if self._show_export:
            handled = self._on_key_export_overlay(event)
            if handled:
                event.stop()
                return

        if self._show_sort:
            handled = self._on_key_sort_overlay(event)
            if handled:
                event.stop()
                return

        if self._show_help and event.key == "escape":
            self.action_toggle_help()
            event.stop()

    def on_mount(self) -> None:
        self._set_active_tab("info")
        self.query_one("#search_input", Input).focus()
        from core.config import load_config
        cfg = load_config()
        self._semantic_enabled = cfg.semantic_search_enabled

    def on_input_changed(self, event: Input.Changed) -> None:
        value = event.value

        # Clear error state when query becomes valid
        if self._input_error and len(value.strip()) >= 3:
            self.query_one("#search_input", Input).remove_class("input-error")
            self._input_error = False
            self.query_one("#status_top", Static).update(
                "RECON  ─────────────────────────────────────────"
            )

        palette = self.query_one("#command_palette", CommandPalette)
        if value.startswith("/") and " " not in value:
            palette.is_active = True
            palette.remove_class("hidden")
            palette.filter(value)
        else:
            palette.is_active = False
            palette.add_class("hidden")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()

        if query == "/theme" or query.startswith("/theme "):
            theme_name = query[6:].strip().lower().replace(" ", "-")
            valid_themes = [
                "arctic-frost", "botanical-garden", "desert-rose", "forest-canopy",
                "golden-hour", "midnight-galaxy", "modern-minimalist", "ocean-depths",
                "sunset-boulevard", "tech-innovation"
            ]
            if not theme_name or theme_name not in valid_themes:
                self.query_one("#status_top", Static).update(
                    f"ERR: Choose theme: {', '.join(valid_themes)}"
                )
                search_input = self.query_one("#search_input", Input)
                search_input.value = "/theme "
                search_input.focus()
                event.stop()
                return

            for cls in list(self.classes):
                if cls.startswith("theme-"):
                    self.remove_class(cls)
            self.add_class(f"theme-{theme_name}")
            self.query_one("#status_top", Static).update(f"Theme changed to {theme_name}")
            search_input = self.query_one("#search_input", Input)
            search_input.value = ""
            event.stop()
            return

        # Input validation: minimum 3 characters
        search_input = self.query_one("#search_input", Input)
        if len(query) < 3:
            search_input.add_class("input-error")
            self._input_error = True
            self.query_one("#status_top", Static).update(
                "ERR: Query must be 3+ characters."
            )
            event.stop()
            return

        if self._input_error:
            search_input.remove_class("input-error")
            self._input_error = False

        self.query_one("#status_top", Static).update(
            f"RECON  ─────────────  Searching: {escape(query)}..."
        )
        sources = list(self._active_sources) if self._active_sources and len(self._active_sources) < len(ALL_SOURCES) else None
        
        # Fire off the worker so the UI remains completely responsive
        self._perform_search(query, sources)
        self.query_one(ResultList).focus()

    @work(exclusive=True)
    async def _perform_search(self, query: str, sources: list | None) -> None:
        """Worker task to perform the search without blocking the UI event handler."""
        import asyncio
        await asyncio.sleep(0.01) # Yield to event loop to guarantee the "Searching..." text renders
        self._results = await search_all(query, sources=sources)

        if self._semantic_enabled and self._results:
            from core.search import semantic_search
            sem_results = await semantic_search(query, top_k=20)
            if sem_results:
                seen = {r.id for r in sem_results}
                rest = [r for r in self._results if r.id not in seen]
                self._results = sem_results + rest[:30]
        
        result_list = self.query_one(ResultList)
        result_list.clear()

        for i, record in enumerate(self._results, 1):
            result_list.mount(ResultListItem(record, i))

        count = len(self._results)
        src_info = ""
        if self._active_sources and len(self._active_sources) < len(ALL_SOURCES):
            active_names = [SOURCE_REGISTRY[s][0] for s in sorted(self._active_sources)]
            src_info = f"  │  sources: {','.join(active_names)}"
            
        semantic_info = "  │  [Semantic]" if self._semantic_enabled else ""
            
        if count == 0:
            self.query_one("#status_top", Static).update(
                "ERR: No patents found. Try: 'battery' or 'solid state'"
            )
        else:
            self.query_one("#status_top", Static).update(
                f"RECON  ──  \"{escape(query)}\"  │  {count} results{src_info}{semantic_info}  │  sort: {self._sort_mode}"
            )

        if self._results:
            result_list.index = 0
            self._load_record(self._results[0])
            result_list.focus()

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and hasattr(event.item, "record"):
            self._load_record(event.item.record)

    def _load_record(self, record) -> None:
        """Update the active preview tab with the given record."""
        try:
            self.query_one(InfoTab).update_record(record)
            self.query_one(ClaimsTab).reset()
            self.query_one(ImageTab).reset()
        except Exception as e:
            self.notify(f"ERR: {escape(str(e))}", severity="error")

        # Lazily load claims/image if those tabs are active
        tab = self._active_tab
        if tab == "claims":
            self.call_after_refresh(self._lazy_load_claims, record)
        elif tab == "image":
            self.call_after_refresh(self._lazy_load_image, record)

        # Trigger background enrichment for the selected patent
        self._enrich_current(record)

    @work(exclusive=True, group="enrichment")
    async def _enrich_current(self, record) -> None:
        from core.enrichment import enrich_patent
        # Check if already has cross_references
        if record.cross_references:
            return
        try:
            await enrich_patent(record)
            self.query_one(InfoTab).update_record(record)
            
            # Refresh the score in the list view
            result_list = self.query_one(ResultList)
            for child in result_list.children:
                if getattr(child, "record", None) is record and hasattr(child, "refresh_score"):
                    child.refresh_score()
                    break

            if record.cross_references:
                self.notify(f"Enrichment: {len(record.cross_references)} signals found", timeout=2.0)
        except Exception as e:
            import logging
            logging.getLogger("recon").error(f"Enrichment error: {e}", exc_info=True)
            self.notify(f"Enrichment error: {e}", severity="error")

    async def _lazy_load_claims(self, record) -> None:
        await self.query_one(ClaimsTab).load_claims(record)

    async def _lazy_load_image(self, record) -> None:
        await self.query_one(ImageTab).load_image(record)

    def _current_record(self):
        result_list = self.query_one(ResultList)
        idx = result_list.index
        if idx is not None and 0 <= idx < len(result_list.children):
            item = result_list.children[idx]
            if hasattr(item, "record"):
                return item.record
        return None

    # ── Tab switching (PRD: h/l, ←/→) ─────────────────
    def action_next_tab(self) -> None:
        idx = (_TABS.index(self._active_tab) + 1) % len(_TABS)
        new_tab = _TABS[idx]
        self._set_active_tab(new_tab)
        record = self._current_record()
        if record and new_tab == "claims":
            self.call_after_refresh(self._lazy_load_claims, record)
        elif record and new_tab == "image":
            self.call_after_refresh(self._lazy_load_image, record)

    def action_prev_tab(self) -> None:
        idx = (_TABS.index(self._active_tab) - 1) % len(_TABS)
        new_tab = _TABS[idx]
        self._set_active_tab(new_tab)
        record = self._current_record()
        if record and new_tab == "claims":
            self.call_after_refresh(self._lazy_load_claims, record)
        elif record and new_tab == "image":
            self.call_after_refresh(self._lazy_load_image, record)

    # ── Detail view (PRD: Enter) ────────────────────────
    def action_open_detail(self) -> None:
        record = self._current_record()
        if record:
            self.app.push_screen(DetailScreen(record))
        else:
            self.notify("No patent selected.")

    # ── Quick open 1-9 ──────────────────────────────────
    def action_quick_open(self, n: str) -> None:
        idx = int(n) - 1
        if 0 <= idx < len(self._results):
            record = self._results[idx]
            self.app.push_screen(DetailScreen(record))
        else:
            self.notify(f"ERR: No result #{n}.")

    # ── Help overlay (PRD: ?) ───────────────────────────
    def action_toggle_help(self) -> None:
        overlay = self.query_one("#help_overlay", Static)
        if self._show_help:
            overlay.add_class("hidden")
        else:
            overlay.remove_class("hidden")
        self._show_help = not self._show_help

    # ── Independent claims toggle (PRD: i) ─────────────
    def action_toggle_independent(self) -> None:
        if self._active_tab == "claims":
            self.query_one(ClaimsTab).toggle_independent()

    # ── Image navigation (PRD: n/p) ────────────────────
    def action_next_figure(self) -> None:
        if self._active_tab == "image":
            self.query_one(ImageTab).next_figure()

    def action_prev_figure(self) -> None:
        if self._active_tab == "image":
            self.query_one(ImageTab).prev_figure()

    # ── Synthesis mode toggle (PRD: m) ─────────────────
    def action_toggle_synthesis(self) -> None:
        if self._results:
            self.app.push_screen(SynthesisScreen(self._results))
        else:
            self.app.notify("No search results to synthesize.")

    # ── Collection actions ──────────────────────────────
    def action_save_collection(self) -> None:
        record = self._current_record()
        if record:
            db = CacheDatabase()
            db.save_to_collection(record)
            self.notify(f"Saved {record.id} to collection.")
        else:
            self.notify("No patent selected.")

    def action_reader_mode(self) -> None:
        record = self._current_record()
        if record:
            self.app.push_screen(ReaderModeScreen(record))

    def action_show_citation_graph(self) -> None:
        record = self._current_record()
        if record:
            self.app.push_screen(CitationGraphScreen(record))

    def _render_export_overlay(self) -> str:
        lines = [
            "┌─ Export Format ──────────────────────────┐",
            "│                                           │",
        ]
        for i, fmt in enumerate(self.EXPORT_FORMATS):
            marker = "●" if i == self._export_selected else " "
            lines.append(f"│  [{marker}] {fmt:<34}│")
        lines += [
            "│                                           │",
            "│  ↑/↓ select  Enter confirm  Esc cancel    │",
            "└───────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def _show_export_overlay(self) -> None:
        self._show_export = True
        self._export_selected = 0
        overlay = self.query_one("#export_overlay", Static)
        overlay.update(self._render_export_overlay())
        overlay.remove_class("hidden")

    def _hide_export_overlay(self) -> None:
        self._show_export = False
        overlay = self.query_one("#export_overlay", Static)
        overlay.add_class("hidden")

    def _confirm_export(self) -> None:
        self._hide_export_overlay()
        fmt = self.EXPORT_FORMATS[self._export_selected]
        from cli.export import export_records
        try:
            db = CacheDatabase()
            records = db.get_collection()
            if not records:
                self.notify("Collection is empty. Nothing to export.")
                return
            export_records(records, fmt, f"collection_export.{fmt}")
            self.notify(f"Exported {len(records)} patents to collection_export.{fmt}")
        except Exception as e:
            self.notify(f"ERR: Export failed: {escape(str(e))}", severity="error")

    def action_export_collection(self) -> None:
        db = CacheDatabase()
        if not db.get_collection():
            self.notify("ERR: Collection is empty. Save patents with 's' first.", severity="error")
            return
        self._show_export_overlay()

    def _on_key_export_overlay(self, event) -> bool:
        """Handle key events when export overlay is visible. Returns True if handled."""
        if event.key == "up":
            self._export_selected = (self._export_selected - 1) % len(self.EXPORT_FORMATS)
            self.query_one("#export_overlay", Static).update(self._render_export_overlay())
            return True
        elif event.key == "down":
            self._export_selected = (self._export_selected + 1) % len(self.EXPORT_FORMATS)
            self.query_one("#export_overlay", Static).update(self._render_export_overlay())
            return True
        elif event.key == "enter":
            self._confirm_export()
            return True
        elif event.key == "escape":
            self._hide_export_overlay()
            return True
        return False

    def action_download_patent(self) -> None:
        record = self._current_record()
        if record:
            self.notify(f"Download queued for {record.id}.")
        else:
            self.notify("No patent selected.")

    # ── Source Filter Overlay ────────────────────────
    def _render_source_filter(self) -> str:
        lines = [
            "┌─ Source Filter ────────────────────────────┐",
            "│  [Space] toggle  [Enter] apply  [Esc] cancel│",
            "│                                             │",
        ]
        for i, src in enumerate(ALL_SOURCES):
            marker = "✓" if src in self._active_sources else " "
            display = SOURCE_REGISTRY[src][0]
            sel = "→" if i == self._source_filter_selected else " "
            lines.append(f"│ {sel}[{marker}] {display:<35}│")
        lines += [
            "│                                             │",
            "│  ↑/↓ navigate  Space toggle  Enter confirm  │",
            "└─────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def _show_source_filter_overlay(self) -> None:
        self._show_source_filter = True
        self._source_filter_selected = 0
        overlay = self.query_one("#source_filter_overlay", Static)
        overlay.update(self._render_source_filter())
        overlay.remove_class("hidden")

    def _hide_source_filter_overlay(self) -> None:
        self._show_source_filter = False
        overlay = self.query_one("#source_filter_overlay", Static)
        overlay.add_class("hidden")

    def action_toggle_source_filter(self) -> None:
        self._show_source_filter_overlay()

    def _on_key_source_filter(self, event) -> bool:
        if event.key == "up":
            self._source_filter_selected = (self._source_filter_selected - 1) % len(ALL_SOURCES)
            self.query_one("#source_filter_overlay", Static).update(self._render_source_filter())
            return True
        elif event.key == "down":
            self._source_filter_selected = (self._source_filter_selected + 1) % len(ALL_SOURCES)
            self.query_one("#source_filter_overlay", Static).update(self._render_source_filter())
            return True
        elif event.key == "space":
            src = ALL_SOURCES[self._source_filter_selected]
            if src in self._active_sources:
                self._active_sources.discard(src)
            else:
                self._active_sources.add(src)
            self.query_one("#source_filter_overlay", Static).update(self._render_source_filter())
            return True
        elif event.key == "enter":
            self._hide_source_filter_overlay()
            count = len(self._active_sources)
            self.app.notify(f"Source filter: {count}/{len(ALL_SOURCES)} active")
            return True
        elif event.key == "escape":
            self._hide_source_filter_overlay()
            return True
        return False

    # ── Sort Overlay ──────────────────────────────────
    def _render_sort_overlay(self) -> str:
        lines = [
            "┌─ Sort & Weights ───────────────────────────┐",
            "│                                            │",
        ]
        options = ["relevance", "date", "assignee", "citation count", "custom (+30 citations)"]
        for i, opt in enumerate(options):
            marker = "●" if opt == self._sort_mode else " "
            sel = "→" if i == self._sort_selected else " "
            lines.append(f"│ {sel}[{marker}] {opt:<34}│")
        lines += [
            "│                                            │",
            "│  ↑/↓ select  Enter confirm  Esc cancel     │",
            "└────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def _show_sort_overlay(self) -> None:
        self._show_sort = True
        self._sort_selected = 0
        overlay = self.query_one("#sort_overlay", Static)
        overlay.update(self._render_sort_overlay())
        overlay.remove_class("hidden")

    def _hide_sort_overlay(self) -> None:
        self._show_sort = False
        overlay = self.query_one("#sort_overlay", Static)
        overlay.add_class("hidden")

    def action_toggle_sort(self) -> None:
        self._show_sort_overlay()

    def _on_key_sort_overlay(self, event) -> bool:
        options = ["relevance", "date", "assignee", "citation count", "custom (+30 citations)"]
        if event.key == "up":
            self._sort_selected = (self._sort_selected - 1) % len(options)
            self.query_one("#sort_overlay", Static).update(self._render_sort_overlay())
            return True
        elif event.key == "down":
            self._sort_selected = (self._sort_selected + 1) % len(options)
            self.query_one("#sort_overlay", Static).update(self._render_sort_overlay())
            return True
        elif event.key == "enter":
            self._sort_mode = options[self._sort_selected]
            self._hide_sort_overlay()
            self.app.notify(f"Sort mode changed to: {self._sort_mode}")
            self._apply_sort()
            return True
        elif event.key == "escape":
            self._hide_sort_overlay()
            return True
        return False

    def _apply_sort(self) -> None:
        if not self._results:
            return
            
        if self._sort_mode == "date":
            self._results.sort(key=lambda r: r.dates.get("filed", "[?]"), reverse=True)
        elif self._sort_mode == "assignee":
            self._results.sort(key=lambda r: r.assignee or "")
        elif self._sort_mode == "citation count":
            # For mockup, just sort by score
            self._results.sort(key=lambda r: len(r.cross_references) if r.cross_references else 0, reverse=True)
        else: # relevance or custom
            from core.scoring import calculate_signal_score
            self._results.sort(key=lambda r: calculate_signal_score(r.cross_references), reverse=True)
            
        result_list = self.query_one(ResultList)
        result_list.clear()
        for i, record in enumerate(self._results, 1):
            result_list.mount(ResultListItem(record, i))
        
        self.query_one("#status_top", Static).update(
            str(self.query_one("#status_top", Static).content).replace(f"sort: {self._sort_mode}", "") + f"sort: {self._sort_mode}"
        )
        if self._results:
            result_list.index = 0
            self._load_record(self._results[0])
            result_list.focus()

    def action_toggle_semantic(self) -> None:
        from core.ai import AIProvider
        from core.config import load_config, save_config

        cfg = load_config()

        if not AIProvider.nomic_is_installed():
            if cfg.nomic_consent_given:
                self.app.notify("Semantic Search unavailable: nomic-embed-text not found. Run 'ollama pull nomic-embed-text'", severity="error")
                return
            self._prompt_nomic_consent()
            return

        self._semantic_enabled = not self._semantic_enabled
        cfg.semantic_search_enabled = self._semantic_enabled
        save_config(cfg)
        state = "enabled" if self._semantic_enabled else "disabled"
        self.app.notify(f"Semantic Search {state}")

        top = self.query_one("#status_top", Static)
        text = str(top.content)
        if self._semantic_enabled and "[Semantic]" not in text:
            top.update(text.replace("results", "results  │  [Semantic]"))
        elif not self._semantic_enabled and "[Semantic]" in text:
            top.update(text.replace("  │  [Semantic]", ""))

    def _prompt_nomic_consent(self) -> None:
        """Show inline consent prompt for nomic-embed-text download (no ModalScreen)."""
        from core.config import load_config, save_config

        overlay = self.query_one("#nomic_consent_overlay", Static)
        overlay.remove_class("hidden")
        overlay.update(
            "[?] Download nomic-embed-text (270MB) for local semantic search? [y/N]: "
        )
        self._awaiting_nomic_consent = True

    @work(exclusive=True, thread=True)
    def _do_pull_nomic(self, cfg) -> None:
        """Pull nomic model in background thread, then re-toggle semantic."""
        import asyncio
        from core.ai import AIProvider
        from core.config import save_config

        async def _pull():
            ok = await AIProvider.pull_nomic()
            return ok

        ok = asyncio.run(_pull())
        if ok:
            cfg.nomic_consent_given = True
            cfg.semantic_search_enabled = True
            save_config(cfg)
            self.app.call_from_thread(lambda: self.app.notify("nomic-embed-text ready. Semantic Search enabled."))
            self._semantic_enabled = True
        else:
            self.app.call_from_thread(lambda: self.app.notify("ERR: Failed to download nomic-embed-text. Check Ollama is running.", severity="error"))

    # ── Overlay dismissal ─────────────────────────────

    def _dismiss_active_overlay(self) -> bool:
        """Dismiss any active overlay. Returns True if an overlay was dismissed."""
        if self._show_export:
            self._hide_export_overlay()
            return True
        if self._show_source_filter:
            self._hide_source_filter_overlay()
            return True
        if self._show_sort:
            self._hide_sort_overlay()
            return True
        if self._show_help:
            self.action_toggle_help()
            return True
        if self._show_assignee_view:
            self.action_toggle_assignee_view()
            return True
        return False

    def action_dismiss_or_quit(self) -> None:
        """Dismiss overlays first, then quit if none active."""
        if self._dismiss_active_overlay():
            return
        self.app.exit()

    # ── Search history cycling ────────────────────────

    def _cycle_search_history(self, direction: int = -1) -> None:
        """Cycle through search history in the given direction (-1 for up)."""
        db = CacheDatabase()
        if not self._search_history:
            self._search_history = db.get_search_history(limit=50)
            self._search_history_index = -1

        if not self._search_history:
            return

        self._search_history_index += direction
        if self._search_history_index < 0:
            self._search_history_index = len(self._search_history) - 1
        elif self._search_history_index >= len(self._search_history):
            self._search_history_index = 0

        entry = self._search_history[self._search_history_index]
        inp = self.query_one("#search_input", Input)
        inp.value = entry.get("query_text", "")
        inp.cursor_position = len(inp.value)

    # ── Jump to top/bottom ────────────────────────────

    def action_jump_to_top(self) -> None:
        """Jump to the top of the result list (g key)."""
        result_list = self.query_one(ResultList)
        if result_list.children:
            result_list.index = 0

    def action_jump_to_bottom(self) -> None:
        """Jump to the bottom of the result list (G key)."""
        result_list = self.query_one(ResultList)
        if result_list.children:
            result_list.index = len(result_list.children) - 1

    # ── Assignee Portfolio View ───────────────────────

    def _build_assignee_view(self) -> str:
        """Build the assignee portfolio view content."""
        assignees: dict[str, int] = {}
        for record in self._results:
            name = record.assignee or "UNKNOWN"
            assignees[name] = assignees.get(name, 0) + 1

        sorted_assignees = sorted(assignees.items(), key=lambda x: -x[1])

        lines = [
            "┌─ Assignee Portfolio View ──────────────────┐",
            "│                                             │",
        ]
        for name, count in sorted_assignees[:15]:
            escaped_name = escape(name[:28])
            lines.append(f"│  {escaped_name:<30} {count:>3} patents │")
        lines += [
            "│                                             │",
            "│  [a] toggle   [Esc/q] dismiss              │",
            "└─────────────────────────────────────────────┘",
        ]
        return "\n".join(lines)

    def action_toggle_assignee_view(self) -> None:
        """Toggle the assignee portfolio view overlay."""
        overlay = self.query_one("#assignee_overlay", Static)
        if self._show_assignee_view:
            overlay.add_class("hidden")
            self._show_assignee_view = False
        else:
            overlay.update(self._build_assignee_view())
            overlay.remove_class("hidden")
            self._show_assignee_view = True

    # ── Responsive breakpoints ────────────────────────

    def on_resize(self, event: Resize) -> None:
        """Adapt layout to terminal width."""
        width = event.size.width
        
        # Ignore transient 0-width resize events during terminal initialization
        if width == 0:
            return
            
        if width < 40:
            self.app.exit(
                return_code=1,
                message="ERR: Terminal too narrow (40+ cols required)."
            )
            return

        result_pane = self.query_one("#result_list")
        tab_pane = self.query_one("#preview_column")

        if width < 80:
            result_pane.styles.width = "100%"
            tab_pane.styles.display = "none"
        else:
            result_pane.styles.width = "40%"
            tab_pane.styles.display = "block"

    def action_focus_search(self) -> None:
        self.query_one("#search_input", Input).focus()

    # ── Command palette methods ────────────────────────────
    def _on_key_command_palette(self, event) -> bool:
        palette = self.query_one("#command_palette", CommandPalette)
        if event.key == "down":
            palette.select_next()
            return True
        elif event.key == "up":
            palette.select_prev()
            return True
        elif event.key == "enter":
            action = palette.selected_action()
            if action:
                self._execute_command(action)
            return True
        elif event.key == "escape":
            palette.is_active = False
            palette.add_class("hidden")
            self.query_one("#search_input", Input).value = ""
            return True
        return False

    def _execute_command(self, action: str) -> None:
        palette = self.query_one("#command_palette", CommandPalette)
        palette.is_active = False
        palette.add_class("hidden")
        self.query_one("#search_input", Input).value = ""

        action_map = {
            "focus_search": lambda: self.query_one("#search_input", Input).focus(),
            "export_collection": self.action_export_collection,
            "save_collection": self.action_save_collection,
            "reader_mode": self.action_reader_mode,
            "show_citation_graph": self.action_show_citation_graph,
            "translate": lambda: self.call_after_refresh(self.action_translate()),
            "toggle_source_filter": self.action_toggle_source_filter,
            "change_theme": lambda: self._insert_slash_command("/theme "),
            "toggle_help": self.action_toggle_help,
            "clear_search": self._clear_search,
            "show_config": self._show_config,
            "quit": self.app.exit,
        }
        handler = action_map.get(action)
        if handler:
            handler()

    def _clear_search(self) -> None:
        self.query_one("#search_input", Input).value = ""
        self.query_one("#search_input", Input).focus()
        self._results = []
        self.query_one(ResultList).clear()
        self.query_one("#status_top", Static).update("RECON  ─────────────────────────────────────────")
        self.notify("Search cleared.")

    def _insert_slash_command(self, cmd: str) -> None:
        input_widget = self.query_one("#search_input", Input)
        input_widget.value = cmd
        input_widget.focus()
        input_widget.cursor_position = len(cmd)

    def _show_config(self) -> None:
        self.notify("Config: ~/.config/recon/config.toml  |  Run 'recon config --help'")

    async def action_translate(self) -> None:
        from core.translation import translate_text
        record = self._current_record()
        if not record:
            self.app.notify("No patent selected.")
            return

        # Toggle: store original on first call, restore on second
        if getattr(record, "_original_abstract", None) is not None:
            record.abstract = record._original_abstract
            record._original_abstract = None
            if self._active_tab == "info":
                self.query_one(InfoTab).update_record(record)
            self.app.notify("Reverted to original.")
            return

        self.app.notify("Translating...")
        record._original_abstract = record.abstract
        translated = await translate_text(record.abstract)
        if translated != record._original_abstract and not translated.startswith("ERR:"):
            record.abstract = translated
            if self._active_tab == "info":
                self.query_one(InfoTab).update_record(record)
            self.app.notify("Translation complete.")
        else:
            record._original_abstract = None
            if translated.startswith("ERR:"):
                self.app.notify(translated, severity="error")
            else:
                self.app.notify("Text already in English.")
