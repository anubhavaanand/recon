# RECON Frontend Specification Document v1.0.0

**Project:** RECON --- Terminal-Native Patent Research Tool  
**Framework:** Textual (Python TUI framework)  
**Design System:** Custom terminal-native aesthetic (k9s + ncspot hybrid)  
**Auth:** No user authentication (OS-level boundary)  
**Target:** Python 3.12+, Linux/macOS terminals  

---

## 1. Page/Route Inventory

RECON is a single-process terminal application. There are no URLs in the web sense. Instead, we define **Screen Routes** --- distinct full-screen views navigable via keyboard shortcuts.

| Screen ID | Trigger | Access Level | Description |
|-----------|---------|--------------|-------------|
| `SearchScreen` | `recon search` (no args) | Always | Primary TUI interface. Search input, result list, three-tab preview |
| `ReaderModeScreen` | `r` hotkey from SearchScreen | Always | Full-width, chrome-free patent reading view |
| `HelpOverlay` | `?` hotkey from SearchScreen | Always | Inline keyboard shortcut reference (not modal) |
| `ExportScreen` | `e` hotkey from SearchScreen | Always | Inline export format selection (not modal) |
| `CLI Search` | `recon search "query"` | Always | Non-interactive table output via `rich`, exits immediately |
| `Config CLI` | `recon config set/show` | Always | Terminal-based configuration management |

**Navigation Rules:**
- No mouse-required interactions. All features accessible via keyboard.
- `Escape` or `q` returns to previous screen (stack-based).
- No modal dialogs ever --- all overlays are inline widgets within the current screen.

---

## 2. Component Hierarchy

### 2.1 Application Root

```
ReconApp (Textual App)
├── CSS (tui/app.css) --- global styles, color variables, dark-mode base
├── Screens
│   ├── SearchScreen (primary)
│   │   ├── SearchInput (Input widget)
│   │   │   └── placeholder="Search patents..."
│   │   ├── ResultList (custom ListView subclass)
│   │   │   ├── ListItem (PatentRecord dataclass attached)
│   │   │   │   └── Static --- title + assignee + date compact line
│   │   │   └── ... (scrollable, keyboard-navigable)
│   │   ├── TabbedContent (Info / Claims / Image)
│   │   │   ├── InfoTab (Static subclass)
│   │   │   │   └── Rich Text --- metadata + abstract + cross-reference signals
│   │   │   ├── ClaimsTab (Static subclass, LAZY-LOADED)
│   │   │   │   └── Rich Text --- claims fetched on first activation only
│   │   │   └── ImageTab (Static subclass, LAZY-LOADED)
│   │   │       └── Rich Text / Sixel / Kitty graphics --- image rendering
│   │   ├── HelpOverlay (Static, initially hidden)
│   │   │   └── ASCII box with shortcut reference
│   │   └── Footer (Textual Footer) --- status line with active shortcuts
│   ├── ReaderModeScreen
│   │   ├── ScrollableContainer (Vertical)
│   │   │   └── Static --- full patent content (title, abstract, claims)
│   │   └── StatusLine (Static) --- "Reader Mode | q: quit | j/k: scroll"
│   └── (future screens: CitationGraphScreen, ConfigScreen)
├── Widgets (shared)
│   ├── ResultList
│   ├── InfoTab
│   ├── ClaimsTab
│   ├── ImageTab
│   └── HelpOverlay
└── Clients (non-visual, but state-relevant)
    ├── USPTOClient
    ├── WIPOClient
    ├── EPOClient (v0.3.0)
    └── IntelligenceClient
```

### 2.2 Widget Responsibilities

| Widget | File | Parent | Responsibility |
|--------|------|--------|----------------|
| `ResultList` | `tui/widgets/result_list.py` | `SearchScreen` | Custom `ListView`. Renders patent summaries. Stores `PatentRecord` on each `ListItem`. Handles `arrow up/down` navigation. |
| `InfoTab` | `tui/widgets/info_tab.py` | `TabbedContent` | Static display of patent metadata (ID, title, assignee, date, status, abstract). Shows cross-reference intelligence signals with confidence scores. |
| `ClaimsTab` | `tui/widgets/claims_tab.py` | `TabbedContent` | Lazy-loaded claims display. Fetches claims text on first tab activation only. Caches result for the session. |
| `ImageTab` | `tui/widgets/image_tab.py` | `TabbedContent` | Terminal image rendering. Probes Kitty -> iTerm2 -> Sixel -> external viewer fallback. Shows placeholder if no image. |
| `HelpOverlay` | `tui/widgets/help_overlay.py` | `SearchScreen` | Inline `Static` widget (NOT `ModalScreen`). Toggles visibility with `?`. Lists all keyboard shortcuts. |

---

## 3. State Management Strategy

### 3.1 State Categories

| State Type | Storage | Scope | Examples |
|------------|---------|-------|----------|
| **Session State** | Python instance variables on `SearchScreen` | Screen lifetime | `current_results: list[PatentRecord]`, `selected_index: int`, `active_tab: str` |
| **UI State** | Textual reactive attributes (`@reactive`) | Widget lifetime | `HelpOverlay.visible`, `ClaimsTab.loaded`, `ImageTab.image_data` |
| **Persistent State** | SQLite (`storage/cache.py`) | Cross-session | Search cache (30-day TTL), collections, API keys, config |
| **Global Config** | `~/.config/recon/config.toml` | Cross-session | API keys, rate limit preferences, default sources |

### 3.2 State Flow Diagram

```
User Input (keyboard)
    |
SearchScreen.on_key / on_input_changed
    |
Session State updated (current_results, selected_index)
    |
Reactive updates trigger UI refresh
    |
ResultList.highlighted_child -> InfoTab.update()
    |
TabbedContent.TabActivated -> lazy-load ClaimsTab / ImageTab
    |
Cache check (SQLite) -> API call if miss -> Store result
    |
UI renders updated content
```

### 3.3 Key State Rules

- **No global mutable state.** Each screen owns its state. Data passes via method arguments, not shared globals.
- **Cache-aside pattern.** Check SQLite before API call. Write back on successful fetch.
- **Lazy loading.** Claims and images fetch only on tab activation, not on search result selection.
- **No React/Zustand/Redux.** Textual's built-in reactive system (`@reactive`, `watch`, `compute`) is sufficient.

### 3.4 Textual Reactive State Example

```python
from textual.reactive import reactive

class SearchScreen(Screen):
    current_results: reactive[list[PatentRecord]] = reactive([])
    selected_record: reactive[PatentRecord | None] = reactive(None)

    def watch_selected_record(self, record: PatentRecord | None) -> None:
        # Auto-update InfoTab when selection changes
        if record:
            info_tab = self.query_one("#info", InfoTab)
            info_tab.update(self._format_info(record))
```

---

## 4. Key User Flows

### 4.1 Flow: Search -> Browse -> Export (Primary Flow)

**Goal:** Find patents, review details, export results.

| Step | Action | Screen | Visual Feedback | State Change |
|------|--------|--------|-----------------|--------------|
| 1 | Launch TUI | `SearchScreen` | Search input focused, cursor blinking | `SearchScreen` mounted |
| 2 | Type query "solid state battery" | `SearchScreen` | Text appears in input | `search_query` updated |
| 3 | Press `Enter` | `SearchScreen` | Loading spinner in footer | `is_searching = True` |
| 4 | Results populate | `SearchScreen` | ResultList shows N patents | `current_results = [...]` |
| 5 | Press `down arrow` to select | `SearchScreen` | Row highlighted, InfoTab updates | `selected_index = 0` |
| 6 | Press `l` or `right arrow` | `SearchScreen` | Tab switches to Claims | `active_tab = "claims"` |
| 7 | Claims lazy-load | `SearchScreen` | "Loading claims..." then text appears | `ClaimsTab.loaded = True` |
| 8 | Press `l` again | `SearchScreen` | Tab switches to Image | `active_tab = "image"` |
| 9 | Image renders | `SearchScreen` | Sixel/Kitty image or placeholder | `ImageTab.image_data = ...` |
| 10 | Press `s` | `SearchScreen` | "Saved US1234567 to collection." | SQLite `collections` table updated |
| 11 | Press `e` | `SearchScreen` | Inline export format selector appears | `ExportOverlay.visible = True` |
| 12 | Select format, `Enter` | `SearchScreen` | "Exported 5 patents to collection_export.json" | File written to disk |
| 13 | Press `q` | Terminal | App exits | Process terminates |

**Latency Budget:**
- Search input -> results: < 3 seconds (cold cache), < 100ms (warm cache)
- Tab switch -> content visible: < 50ms (Info), < 500ms (Claims, lazy), < 1s (Image, lazy)
- Keyboard response: < 16ms (60fps equivalent)

### 4.2 Flow: Reader Mode (Distraction-Free Reading)

**Goal:** Read a single patent without UI chrome.

| Step | Action | Screen | Visual Feedback |
|------|--------|--------|-----------------|
| 1 | Highlight patent in ResultList | `SearchScreen` | Patent selected |
| 2 | Press `r` | `SearchScreen` -> `ReaderModeScreen` | Full-screen patent content, no header/footer |
| 3 | Press `j` / `k` | `ReaderModeScreen` | Content scrolls up/down |
| 4 | Press `Escape` or `q` | `ReaderModeScreen` -> `SearchScreen` | Returns to search, same selection preserved |

### 4.3 Flow: CLI Search (Non-Interactive)

**Goal:** Quick patent lookup, scriptable, automation-friendly.

| Step | Action | Output | Exit Code |
|------|--------|--------|-----------|
| 1 | Run `recon search "solid state battery"` | Terminal | 0 |
| 2 | Results render as `rich` table | 3 rows: ID, Title, Date, Source | 0 |
| 3 | Auto-save to collection | SQLite updated silently | 0 |
| 4 | Process exits | Terminal prompt returns | 0 |

**Error Flow:**
- No results -> "ERR: No patents found for 'solid state battery'. Try broader terms." -> Exit 1
- API failure -> "ERR: USPTO API unavailable (429). Cached results: 0." -> Exit 1
- Invalid query -> "ERR: Query must be at least 3 characters." -> Exit 2

### 4.4 Flow: Configuration

**Goal:** Set API keys and preferences.

| Step | Action | Command | Feedback |
|------|--------|---------|----------|
| 1 | Set USPTO key | `recon config set --uspto-key XXX` | "USPTO API key stored." |
| 2 | Verify | `recon config show` | Masked keys displayed |
| 3 | Search uses key | `recon search "query"` | Live USPTO data returned |

---

## 5. Form Specifications

RECON has no traditional web forms. Instead, we define **Input Interfaces** --- all terminal-native.

### 5.1 Search Input

| Attribute | Specification |
|-----------|---------------|
| **Widget** | `Input` (Textual) |
| **ID** | `#search-input` |
| **Placeholder** | `Search patents...` |
| **Validation** | Min 3 characters, max 200 characters |
| **Error State** | Red border, footer message: "ERR: Query must be 3+ characters." |
| **Success State** | Results populate ResultList, footer shows "N patents found (X.Ys)" |
| **Hotkey** | `/` focuses input from anywhere in SearchScreen |
| **Submit** | `Enter` triggers search |

### 5.2 Export Format Selector

| Attribute | Specification |
|-----------|---------------|
| **Widget** | Inline `Static` overlay (NOT modal) |
| **ID** | `#export-overlay` |
| **Options** | `json`, `csv`, `bibtex`, `markdown`, `pdf` |
| **Navigation** | `up/down` to select, `Enter` to confirm, `Escape` to cancel |
| **Error State** | "ERR: Collection is empty. Save patents with 's' first." |
| **Success State** | "Exported N patents to collection_export.<format>" |
| **Default** | `json` |

### 5.3 Config Key Input (CLI)

| Attribute | Specification |
|-----------|---------------|
| **Widget** | Typer CLI arguments |
| **Command** | `recon config set --uspto-key <key>` |
| **Validation** | Non-empty string, stored with 0600 permissions |
| **Error State** | "ERR: Key cannot be empty." |
| **Success State** | "USPTO API key stored in ~/.config/recon/config.toml" |

---

## 6. Loading & Error States

### 6.1 Loading States

| Scenario | Visual Indicator | Location | Duration Target |
|----------|-------------------|----------|-----------------|
| Search in progress | Spinner + "Searching..." | Footer | < 3s |
| Claims loading | "Loading claims..." | ClaimsTab content area | < 500ms |
| Image loading | "Rendering image..." | ImageTab content area | < 1s |
| Export in progress | "Exporting..." | Footer | < 2s |
| Cache read | (silent) | --- | < 50ms |

**Loading State Rules:**
- Always show loading indicator if operation > 100ms.
- Never block the UI thread --- use `asyncio` for I/O.
- Loading text uses `dim` CSS class (subdued color).
- Cancelable operations: `Escape` aborts search if supported by API client.

### 6.2 Error States

| Scenario | Display | Voice | Action |
|----------|---------|-------|--------|
| API 429 (rate limit) | Footer: "ERR: USPTO rate limited. Retrying in 2s..." | Dry, actionable | Auto-backoff 1s->2s->4s->8s |
| API 401/403 (auth) | Footer: "ERR: USPTO key invalid. Run: recon config set --uspto-key" | Dry, actionable | Prompt for reconfiguration |
| No results | Footer: "ERR: No patents found. Try: 'battery' or 'solid state'" | Dry, actionable | Suggest broader terms |
| Network timeout | Footer: "ERR: USPTO timeout (10s). Check connection." | Dry, actionable | Fail after max retries |
| Cache corruption | Footer: "ERR: Cache corrupted. Rebuilding..." | Dry, actionable | Auto-rebuild from APIs |
| Invalid query | Input border red, footer: "ERR: Query must be 3+ characters." | Dry, actionable | Block submission |
| Empty collection export | Footer: "ERR: Collection is empty. Press 's' to save patents." | Dry, actionable | Guide to save first |
| Image render failure | ImageTab: "Image unavailable. URL: <link>" | Dry, actionable | Show URL for external open |

**Error Voice Constitution:**
- **Prefix:** All errors start with `ERR:`
- **No stacktraces** in standard output (log to `~/.local/share/recon/errors.log`)
- **No generic messages** --- every error tells the user what happened and what to do
- **No exclamation marks** --- dry, mechanical tone
- **Correct:** `ERR: USPTO API unavailable (429). Retry in 2s.`
- **Incorrect:** `Oops! Something went wrong. Please try again later.`

### 6.3 Global Error Handler

```python
# In tui/app.py or tui/screens.py
async def on_error(self, error: Exception, context: str) -> None:
    # Global error handler --- never swallows errors silently
    error_msg = f"ERR: {context} failed. {str(error)}"
    self.notify(error_msg, severity="error", timeout=5)
    # Log full traceback for debugging
    logger.exception(f"Error in {context}: {error}")
```

---

## 7. Responsive Breakpoints & Behavior

### 7.1 Terminal Size Adaptation

RECON adapts to terminal dimensions, not device pixels. No CSS media queries --- instead, Textual's `Grid` and `Horizontal`/`Vertical` layouts handle resizing.

| Terminal Size | Layout Mode | Behavior |
|---------------|-------------|----------|
| **>= 120 cols, >= 40 rows** | Full | Three-pane: Search (top), ResultList (left 40%), Tabs (right 60%). ImageTab renders inline images. |
| **80-119 cols, >= 30 rows** | Compact | ResultList (left 50%), Tabs (right 50%). ImageTab shows URL + dimensions only. |
| **< 80 cols or < 30 rows** | Minimal | Stacked vertical: Search -> ResultList -> Tabs (one visible at a time). ImageTab disabled. |
| **< 40 cols** | Unsupported | Exit with: "ERR: Terminal too narrow (40+ cols required)." |

### 7.2 Layout Rules

- **ResultList minimum width:** 35 columns (enough for ID + truncated title)
- **Tab content minimum width:** 40 columns (enough for readable abstract)
- **ImageTab fallback:** If terminal doesn't support graphics protocols, show URL + "Open externally: xdg-open <url>"
- **Footer always visible:** 1 row at bottom, shows status + active shortcuts

### 7.3 Resize Handling

```python
# In SearchScreen
def on_resize(self, event: Resize) -> None:
    # Adapt layout to terminal size
    if event.size.width < 80:
        self.query_one("#result-pane").styles.width = "100%"
        self.query_one("#tab-pane").styles.display = "none"
    else:
        self.query_one("#result-pane").styles.width = "40%"
        self.query_one("#tab-pane").styles.display = "block"
```

---

## 8. Accessibility Requirements

### 8.1 WCAG Target: WCAG 2.1 Level A (Terminal-Adapted)

Terminals have different accessibility constraints than web browsers. We adapt WCAG principles:

| WCAG Principle | Terminal Implementation | Status |
|----------------|-------------------------|--------|
| **1.1 Text Alternatives** | All images have text descriptions in InfoTab | OK |
| **1.3 Adaptable** | Layout reflows at 80/120 col breakpoints | OK |
| **1.4 Distinguishable** | Color not sole indicator --- symbols + text always | OK |
| **2.1 Keyboard Accessible** | All features via keyboard. No mouse required. | OK |
| **2.2 Enough Time** | No auto-timeout. User controls all pacing. | OK |
| **2.3 Seizures** | No flashing content. Static terminal output. | OK |
| **2.4 Navigable** | `Tab` / `Shift+Tab` cycles focus. Arrow keys navigate lists. | OK |
| **3.1 Readable** | Plain English. No jargon without explanation. | OK |
| **3.2 Predictable** | Consistent shortcuts. `q` always quits current view. | OK |
| **3.3 Input Assistance** | Error prevention: confirm destructive actions. | OK |
| **4.1 Compatible** | Standard terminal sequences. No proprietary extensions. | OK |

### 8.2 Terminal-Specific Accessibility

| Feature | Implementation |
|---------|----------------|
| **Screen reader support** | All content is text-based. Screen readers (Orca, VoiceOver) can read terminal output. |
| **High contrast mode** | Respects `$COLORFGBG` environment variable. Uses bold + underline as secondary indicators. |
| **Colorblind-safe** | Red/green not used for critical status. Symbols: `OK` success, `X` error, `?` unknown. |
| **Font size independence** | Terminal font size controlled by user. RECON uses relative sizing (percentages, not fixed cells). |
| **Motion sensitivity** | No animations. Instant state changes only. |

### 8.3 Keyboard Navigation Map

| Key | Action | Context |
|-----|--------|---------|
| `Tab` | Next focusable widget | Global |
| `Shift+Tab` | Previous focusable widget | Global |
| `Up/Down` | Navigate ResultList | SearchScreen |
| `Enter` | Select / Submit | Global |
| `Escape` | Cancel / Back / Quit overlay | Global |
| `q` | Quit current screen | Global |
| `h` / `l` | Previous / Next tab | SearchScreen |
| `j` / `k` | Scroll down / up | ReaderModeScreen |
| `g` / `G` | Top / Bottom of list | ResultList |
| `/` | Focus search input | SearchScreen |
| `?` | Toggle help overlay | SearchScreen |

---

## 9. Performance Targets

### 9.1 Latency Budgets

| Operation | Target | Measurement Method |
|-----------|--------|-------------------|
| **First paint (TUI launch)** | < 100ms | `time recon search` to interactive prompt |
| **Search cold start** | < 3.0s | `Enter` press to ResultList populated |
| **Search warm start (cached)** | < 100ms | `Enter` press to ResultList populated |
| **Tab switch (Info)** | < 16ms | `l` press to content visible |
| **Tab switch (Claims, lazy)** | < 500ms | First activation to claims text visible |
| **Tab switch (Image, lazy)** | < 1.0s | First activation to image rendered |
| **Keyboard response** | < 16ms | Key press to visual feedback |
| **Export (100 patents)** | < 2.0s | `e` + `Enter` to file written |
| **Collection save** | < 50ms | `s` press to SQLite commit |
| **Memory footprint** | < 128MB | `psutil.Process().memory_info().rss` |
| **Startup time (CLI)** | < 500ms | `time recon search "query"` to exit |

### 9.2 Rendering Performance

| Target | Implementation |
|--------|----------------|
| **60fps navigation** | Textual's reactive system batches updates. No DOM thrashing. |
| **Lazy loading** | Claims and images fetch only on first tab activation. |
| **Virtual scrolling** | ResultList uses Textual's built-in virtual scrolling (handles 10,000+ items). |
| **Image optimization** | Images downscaled to terminal dimensions before rendering. No full-resolution transfer. |
| **Cache priority** | L1 (session dict) -> L2 (SQLite) -> L3 (API). 90%+ cache hit rate for repeated queries. |

### 9.3 Profiling Checklist

```bash
# Run these before each release
python -m cProfile -o profile.stats -m recon search "solid state battery"
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumtime'); p.print_stats(20)"

# Memory profiling
python -m memory_profiler cli/main.py search "solid state battery"

# Terminal benchmark
hyperfine --warmup 3 'recon search "solid state battery"'
```

---

## 10. API Integration Points

### 10.1 Data Flow: Component -> Client -> API

| Component | Calls | Client Method | API Endpoint | Auth |
|-----------|-------|---------------|--------------|------|
| `SearchScreen.on_input_submitted` | -> | `search_all(query, sources)` | Multiple | Various |
| `search_all` | -> | `USPTOClient.search(query)` | `GET /api/v1/patents/search` | `X-API-KEY` |
| `search_all` | -> | `WIPOClient.search(query)` | `GET /patentscope/search` | None |
| `search_all` | -> | `EPOClient.search(query)` | `GET /3.2/published-data/search` | OAuth 2.0 |
| `ClaimsTab.on_mount` (lazy) | -> | `USPTOClient.get_claims(patent_id)` | `GET /api/v1/patents/{id}/claims` | `X-API-KEY` |
| `ImageTab.on_mount` (lazy) | -> | `USPTOClient.get_image_url(patent_id)` | `GET /api/v1/patents/{id}/images` | `X-API-KEY` |
| `InfoTab.update` | -> | `IntelligenceClient.get_signals(record)` | Multiple (NIH/NSF/SEC/etc.) | Various |
| `action_save_collection` | -> | `CacheDatabase.save_to_collection(record)` | SQLite `INSERT` | N/A |
| `action_export` | -> | `export_records(records, format)` | File system write | N/A |
| `CacheDatabase.search` | -> | `sqlite3.execute()` | Local SQLite | N/A |

### 10.2 Rate Limiting Integration

| API | Limit | Headroom | Effective Rate | Backoff Strategy |
|-----|-------|----------|----------------|------------------|
| USPTO | 100/min | 24% | 76/min | Token bucket, 1s->2s->4s->8s |
| WIPO | 100/day | 24% | 76/day | Token bucket, 1s->2s->4s->8s |
| EPO | 4/sec | 24% | 3/sec | Token bucket, 1s->2s->4s->8s |
| Intelligence | 10/min | 24% | 8/min | Token bucket, 1s->2s->4s->8s |

**Integration Rule:** Every client call passes through `TokenBucket.acquire()` before HTTP request. Rate limit state is shared per API key (stored in memory, not persistent).

### 10.3 Cache Integration

```python
# Pseudocode for cache-aside pattern
async def search_with_cache(query: str, sources: list[str]) -> list[PatentRecord]:
    query_hash = sha256(query.encode()).hexdigest()

    # L1: Session cache
    if query_hash in session_cache:
        return session_cache[query_hash]

    # L2: SQLite cache (30-day TTL)
    cached = db.get_search_results(query_hash)
    if cached and not expired:
        session_cache[query_hash] = cached
        return cached

    # L3: Live APIs
    results = await asyncio.gather(*[client.search(query) for client in sources])
    merged = sort_and_merge_results(results)

    # Write-through
    db.save_search_results(query_hash, merged)
    session_cache[query_hash] = merged
    return merged
```

### 10.4 Error Handling at Integration Points

| Integration Point | Error | Component Response |
|-------------------|-------|-------------------|
| `USPTOClient.search` | 429 | Retry with backoff, notify user |
| `USPTOClient.search` | 401 | "ERR: USPTO key invalid. Run: recon config set --uspto-key" |
| `WIPOClient.search` | Timeout | "ERR: WIPO timeout. Results may be incomplete." |
| `EPOClient.search` | OAuth expiry | Auto-refresh token, retry once |
| `IntelligenceClient` | Any | Log error, display "[?]" for signal, don't block UI |
| `CacheDatabase` | Corruption | "ERR: Cache corrupted. Rebuilding from APIs." |
| `Image rendering` | Unsupported terminal | "Image rendering requires Kitty/iTerm2. URL: <link>" |

---

## 11. CSS Styling Specification

### 11.1 Color Palette (Dark Mode Default)

```css
/* tui/app.css */
/* Primary colors */
$primary: #7aa2f7;        /* Blue --- active elements, links */
$secondary: #bb9af7;      /* Purple --- secondary info */
$accent: #e0af68;         /* Orange --- highlights, notifications */
$success: #9ece6a;        /* Green --- success states */
$error: #f7768e;          /* Red --- errors */
$warning: #e0af68;        /* Orange --- warnings */
$info: #7dcfff;           /* Cyan --- info */

/* Neutral colors */
$bg: #1a1b26;             /* Background */
$bg-secondary: #24283b;   /* Secondary background */
$fg: #a9b1d6;             /* Foreground text */
$fg-dim: #565f89;         /* Dimmed text */
$border: #414868;         /* Borders */

/* Widget-specific */
ResultList { background: $bg-secondary; border: solid $border; }
ResultList:focus { border: solid $primary; }
ResultList > ListItem:hover { background: $bg; }
ResultList > ListItem.--highlight { background: $primary; color: $bg; }

InfoTab, ClaimsTab, ImageTab { background: $bg; padding: 1 2; }
HelpOverlay { display: none; background: $bg-secondary; border: solid $accent; padding: 1 2; }
HelpOverlay.visible { display: block; }
Footer { background: $bg-secondary; color: $fg-dim; height: 1; }
```

### 11.2 Typography

| Element | Style | Color |
|---------|-------|-------|
| Patent title | Bold | `$primary` |
| Patent ID | Monospace | `$secondary` |
| Assignee | Italic | `$fg` |
| Date | Normal | `$fg-dim` |
| Abstract | Normal, wrapped | `$fg` |
| Claims | Normal, numbered | `$fg` |
| Error messages | Bold | `$error` |
| Success messages | Bold | `$success` |
| Loading text | Italic, dim | `$fg-dim` |

---

## 12. File Structure

```
tui/
├── __init__.py
├── app.py              # ReconApp class, CSS loading, screen routing
├── screens.py          # SearchScreen, ReaderModeScreen
└── widgets/
    ├── __init__.py
    ├── result_list.py  # ResultList (ListView subclass)
    ├── info_tab.py     # InfoTab (Static subclass)
    ├── claims_tab.py   # ClaimsTab (Static, lazy-loaded)
    ├── image_tab.py    # ImageTab (Static, terminal image rendering)
    └── help_overlay.py # HelpOverlay (Static, toggleable)
```

---

## 13. Testing Strategy (Frontend)

| Test Category | File | Coverage Target |
|---------------|------|-----------------|
| Widget rendering | `tests/test_tui_layout.py` | All widgets mount without error |
| Keyboard navigation | `tests/test_tui_navigation.py` | All shortcuts trigger correct actions |
| Tab switching | `tests/test_lazy_loading.py` | Claims/Image lazy-load on first activation |
| Terminal protocols | `tests/test_terminal_protocols.py` | Kitty/iTerm2/Sixel detection |
| Reader mode | `tests/test_reader_mode.py` | Chrome-free, scrollable, `q` exits |
| Help overlay | `tests/test_help_overlay.py` | Toggle with `?`, inline not modal |
| Error states | `tests/test_error_handling.py` | All error paths show `ERR:` prefix |
| Performance | `tests/test_performance.py` | < 3s search, < 100ms navigation |

---

## 14. Appendix: Constitutional Compliance Checklist

| Principle | Frontend Implementation | Verified |
|-----------|------------------------|----------|
| **Zero-AI default** | No AI in UI layer. Scores are deterministic rapidfuzz. | pending |
| **Minimal dependencies** | Textual only. No rich, no prompt-toolkit, no npyscreen. | pending |
| **Keyboard-first** | All features via keyboard. Mouse optional. | pending |
| **No modal dialogs** | HelpOverlay is inline Static. Export is inline. | pending |
| **Dry error voice** | All errors: `ERR: <what> <why> <fix>`. No exclamations. | pending |
| **Speed over depth** | Lazy loading, cache priority, < 3s cold search. | pending |
| **Transparency** | Intelligence signals show source + confidence. | pending |
| **Equal weights** | Score displayed as raw count (+20/signal), not black-box. | pending |
| **Terminal-native** | No web fallback, no GUI fallback, no Docker. | pending |
| **Deterministic** | Same query -> same results (cache TTL permitting). | pending |

---

*Document Version: 1.0.0*  
*Last Updated: 2026-06-22*  
*Author: RECON Architecture Team*  
*Next Review: v0.3.0 release*
