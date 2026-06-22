# RECON — GitHub Issues Breakdown v2.0.0
# Terminal-Native Patent Research Tool
# Generated: 2026-06-22
# Team Size: Solo (1 developer + AI agents)
# Timeline: 12 weeks total (8 weeks elapsed, 4 weeks remaining)
# Current Version: v0.2.0 (live APIs integrated)

---

## Milestone 0: Foundation (COMPLETED)

### M0-T01: Initialize Python 3.12+ project structure
- **Type:** chore
- **Priority:** P0
- **Description:** Bootstrap the RECON project with the six-module architecture (cli/, tui/, core/, clients/, storage/, tests/). Configure pytest with pytest-asyncio. Establish the constitutional constraint of minimal dependencies.
- **Acceptance Criteria:**
  - Directory structure matches: cli/, tui/, tui/widgets/, core/, clients/, storage/, tests/
  - pyproject.toml exists with requires-python >= 3.12
  - pytest.ini configured with asyncio_mode = auto
  - `pip install -e .` succeeds without errors
  - No dependencies beyond: textual, httpx, Pillow, rapidfuzz, typer, fpdf2, tomli/tomli-w
- **Dependencies:** None
- **Estimated Effort:** XS
- **Status:** Complete

### M0-T02: Define PatentRecord and CrossReference dataclasses
- **Type:** feature
- **Priority:** P0
- **Description:** Create the core data models using stdlib dataclasses only (no Pydantic per constitution). PatentRecord must hold all patent metadata fields. CrossReference tracks external intelligence signals.
- **Acceptance Criteria:**
  - `core/models.py` defines `PatentRecord` with fields: id, title, abstract, claims, assignee, inventor, filing_date, publication_date, status, patent_family, citations, image_url, source_api, raw_data
  - `core/models.py` defines `CrossReference` with fields: source, confidence, signal_type, url, matched_entity
  - All fields have type hints
  - `__repr__` produces dry, readable output (no stacktraces)
  - `to_dict()` and `from_dict()` methods for JSON serialization
  - Tests in `tests/test_models.py` verify serialization roundtrip
- **Dependencies:** M0-T01
- **Estimated Effort:** XS
- **Status:** Complete

### M0-T03: Implement SQLite cache schema
- **Type:** feature
- **Priority:** P0
- **Description:** Build the storage layer using stdlib sqlite3. Schema must support document_content, status_metadata, citations, family_links tables. Use JSON columns for semi-structured patent data to avoid migration fragility when APIs change.
- **Acceptance Criteria:**
  - `storage/cache.py` defines `CacheDatabase` class
  - Tables created on init: document_content, status_metadata, citations, family_links, search_results, collections
  - search_results table uses SHA256(query_hash) as primary key for deterministic cache hits
  - 30-day TTL enforced via timestamp comparison
  - JSON serialization for PatentRecord in collections table
  - `save_search_results()`, `get_search_results()`, `is_cache_valid()` methods implemented
  - Tests in `tests/test_cache.py` verify init and basic operations
- **Dependencies:** M0-T02
- **Estimated Effort:** S
- **Status:** Complete

### M0-T04: Create httpx async client with exponential backoff
- **Type:** feature
- **Priority:** P0
- **Description:** Build the base HTTP client in `clients/base.py` using httpx.AsyncClient. Implement 1s->2s->4s->8s auto-backoff for 429/5xx responses. This is the foundation for all API integrations.
- **Acceptance Criteria:**
  - `clients/base.py` defines `BaseClient` with shared `httpx.AsyncClient` instance (singleton pattern)
  - `get_with_backoff()` method accepts url, params, headers, max_retries=4
  - Backoff delays: 1s, 2s, 4s, 8s on 429/503/504 status codes
  - Max 4 retries before raising exception with ERR: prefix message
  - Connection pooling enabled via shared AsyncClient
  - Tests in `tests/test_client.py` verify backoff behavior with mocked responses
- **Dependencies:** M0-T01
- **Estimated Effort:** S
- **Status:** Complete

### M0-T05: Add foundational test suite
- **Type:** chore
- **Priority:** P0
- **Description:** Establish testing infrastructure with pytest, pytest-asyncio, and asyncio fixtures. Create initial test files for models, cache, and client. Target: 100% coverage on core modules.
- **Acceptance Criteria:**
  - `tests/test_models.py` with >= 3 tests
  - `tests/test_cache.py` with >= 3 tests
  - `tests/test_client.py` with >= 2 tests
  - All tests pass with `pytest -xvs`
  - Test execution time < 5 seconds
  - No external network calls in tests (mocked)
- **Dependencies:** M0-T01, M0-T02, M0-T03, M0-T04
- **Estimated Effort:** XS
- **Status:** Complete

---

## Milestone 1: Core Search (COMPLETED)

### M1-T06: Implement USPTO mock client
- **Type:** feature
- **Priority:** P0
- **Description:** Create `USPTOClient` in `clients/patent_apis.py` with mock data for initial development. Must return PatentRecord instances matching the core model schema.
- **Acceptance Criteria:**
  - `USPTOClient` class exists with `search(query, limit=10)` async method
  - Returns list[PatentRecord] with realistic mock data
  - Mock data includes: patent number, title, abstract, assignee, filing date
  - `search()` accepts query string and limit parameter
  - Tests in `tests/test_patent_apis.py` verify mock response structure
- **Dependencies:** M0-T02, M0-T04
- **Estimated Effort:** XS
- **Status:** Complete

### M1-T07: Implement EPO, WIPO, Lens, Google Patents mock clients
- **Type:** feature
- **Priority:** P0
- **Description:** Create mock clients for remaining four APIs. Each must conform to the same interface as USPTOClient for seamless aggregation.
- **Acceptance Criteria:**
  - `EPOClient`, `WIPOClient`, `LensClient`, `GooglePatentsClient` classes exist
  - All implement `search(query, limit=10) -> list[PatentRecord]`
  - Mock data differentiated by source (different patent numbers, assignees)
  - Consistent error handling: return [] on failure with ERR: log message
  - Tests verify all five mock clients
- **Dependencies:** M1-T06
- **Estimated Effort:** S
- **Status:** Complete

### M1-T08: Build search aggregation with asyncio.gather
- **Type:** feature
- **Priority:** P0
- **Description:** Implement `search_all()` in `core/search.py` that concurrently queries all configured APIs using asyncio.gather. Must enforce descending sort and never silently drop entries.
- **Acceptance Criteria:**
  - `core/search.py` defines `search_all(query, sources=None, limit=10)` async function
  - Uses `asyncio.gather()` for concurrent API calls
  - Results merged and sorted by filing_date descending
  - No entries dropped silently (all valid results included)
  - Missing data flagged: None -> [?] or UNKNOWN in output
  - Configurable source list (default: all available)
  - Tests in `tests/test_search.py` verify sort order and merge logic
- **Dependencies:** M1-T06, M1-T07
- **Estimated Effort:** S
- **Status:** Complete

### M1-T09: Create ResultList and InfoTab Textual widgets
- **Type:** feature
- **Priority:** P0
- **Description:** Build the first TUI widgets. ResultList displays patent search results as a scrollable ListView. InfoTab shows basic patent metadata in a Static widget.
- **Acceptance Criteria:**
  - `tui/widgets/result_list.py` defines `ResultList(ListView)` with custom ListItem
  - Each ListItem stores the full PatentRecord in a `record` attribute
  - `tui/widgets/info_tab.py` defines `InfoTab(Static)` with `update(record)` method
  - InfoTab displays: ID, Title, Assignee, Filed, Status, Abstract
  - Uses Rich markup for formatting ([b]bold[/b], etc.)
  - Tests in `tests/test_tui_navigation.py` verify widget creation
- **Dependencies:** M0-T02, M1-T08
- **Estimated Effort:** S
- **Status:** Complete

### M1-T10: Wire SearchScreen with keyboard navigation
- **Type:** feature
- **Priority:** P0
- **Description:** Build the main search screen in `tui/screens.py`. Integrate ResultList and InfoTab. Implement keyboard navigation: arrow keys to navigate results, Enter to search, q to quit.
- **Acceptance Criteria:**
  - `SearchScreen` class exists with compose() yielding search input, ResultList, TabbedContent
  - `BINDINGS` includes: up/down (navigate), enter (search), q (quit)
  - Search input captures query and triggers `search_all()`
  - Results populate ResultList on completion
  - Preview updates in InfoTab when selection changes
  - <100ms preview update target (measured via logging)
  - Tests verify bindings and basic navigation
- **Dependencies:** M1-T09
- **Estimated Effort:** M
- **Status:** Complete

### M1-T11: Integrate typer CLI entrypoint
- **Type:** feature
- **Priority:** P0
- **Description:** Create `cli/main.py` with typer app. Implement `recon search` command that launches the TUI. Add pyproject.toml entry point so `recon` command is available after pip install.
- **Acceptance Criteria:**
  - `cli/main.py` defines `typer.Typer()` app
  - `recon search` command launches SearchScreen via Textual app
  - `pyproject.toml` has `[project.scripts]` with `recon = "cli.main:app"`
  - `pip install -e .` makes `recon` command available in shell
  - `recon --help` shows available commands
  - Tests verify CLI entry point
- **Dependencies:** M1-T10
- **Estimated Effort:** XS
- **Status:** Complete

---

## Milestone 2: Three-Tab Preview (COMPLETED)

### M2-T12: Implement ClaimsTab with lazy loading
- **Type:** feature
- **Priority:** P0
- **Description:** Create `ClaimsTab(Static)` widget that displays patent claims. Claims must be lazy-loaded: only fetched when the user activates the Claims tab, not on initial search.
- **Acceptance Criteria:**
  - `tui/widgets/claims_tab.py` defines `ClaimsTab(Static)`
  - `load(record)` async method fetches claims on demand
  - Claims displayed as numbered list (1. Claim text...)
  - If claims not available, shows "Claims not available." (dry voice)
  - Loading indicator shown while fetching (spinner or "Loading...")
  - Tests in `tests/test_claims_lazy_load.py` verify lazy behavior
- **Dependencies:** M1-T09
- **Estimated Effort:** S
- **Status:** Complete

### M2-T13: Implement ImageTab with terminal image protocols
- **Type:** feature
- **Priority:** P0
- **Description:** Create `ImageTab(Static)` widget for patent diagrams. Must detect terminal capabilities: Kitty > iTerm2 > Sixel > Fallback (external viewer or URL display).
- **Acceptance Criteria:**
  - `tui/widgets/image_tab.py` defines `ImageTab(Static)`
  - `detect_terminal_protocol()` checks: KITTY_WINDOW_ID, TERM_PROGRAM, TERM, COLORTERM
  - Priority: Kitty graphics protocol > iTerm2 inline images > Sixel > external viewer
  - `render_image()` method uses Pillow to convert patent images to terminal format
  - Fallback: display image URL with message "Open with xdg-open [url]"
  - Tests in `tests/test_terminal_protocols.py` verify detection logic
  - Tests in `tests/test_lazy_loading.py` verify image lazy loading
- **Dependencies:** M1-T09
- **Estimated Effort:** M
- **Status:** Complete

### M2-T14: Add TabbedContent with Info/Claims/Image tabs
- **Type:** feature
- **Priority:** P0
- **Description:** Integrate InfoTab, ClaimsTab, and ImageTab into a TabbedContent container in SearchScreen. Handle tab switching events to trigger lazy loading.
- **Acceptance Criteria:**
  - `SearchScreen.compose()` yields `TabbedContent` with three `TabPane`s: info, claims, image
  - Tab IDs: "info-tab", "claims-tab", "image-tab" (or matching widget IDs)
  - `on_tabbed_content_tab_activated` event handler calls `_load_active_tab()`
  - `_load_active_tab(tab_id, record)` strips `--content-tab-` prefix if present
  - Calls `.update()` on Static widgets (not non-existent custom methods)
  - Only active tab loads data; inactive tabs remain empty
  - `l`/`h` or left/right arrow keys switch tabs
- **Dependencies:** M2-T12, M2-T13
- **Estimated Effort:** S
- **Status:** Complete (with fixes applied)

### M2-T15: Fix ListView item access bug
- **Type:** bug
- **Priority:** P0
- **Description:** CRITICAL BUG: `ListView` does not have `get_item_at()` method. Code crashes with AttributeError when switching tabs, saving collections, opening reader mode, or downloading patents.
- **Acceptance Criteria:**
  - All occurrences of `result_list.get_item_at(result_list.index)` replaced
  - Use `result_list.children[result_list.index]` with bounds check: `0 <= index < len(children)`
  - OR use `result_list.highlighted_child` (official Textual API)
  - Fixed in 4 methods: `on_tabbed_content_tab_activated`, `action_save_collection`, `action_reader_mode`, `action_download_patent`
  - TUI no longer crashes on tab switch, save, reader mode, or download
  - Tests pass after fix
- **Dependencies:** M2-T14
- **Estimated Effort:** XS
- **Status:** Complete (fixed via `highlighted_child`)

### M2-T16: Fix tab ID prefix stripping
- **Type:** bug
- **Priority:** P0
- **Description:** Textual automatically prefixes TabPane IDs with `--content-tab-`. `_load_active_tab()` must strip this prefix to match widget IDs correctly.
- **Acceptance Criteria:**
  - `_load_active_tab()` checks `if tab_id.startswith("--content-tab-"):`
  - Strips prefix: `tab_id = tab_id.replace("--content-tab-", "")`
  - Matches against "info", "claims", "image" (not prefixed IDs)
  - Preview tabs populate with data when switched
  - No silent failures (no `except: pass` that hides errors)
- **Dependencies:** M2-T14, M2-T15
- **Estimated Effort:** XS
- **Status:** Complete

---

## Milestone 3: Cross-Reference Intelligence (COMPLETED)

### M3-T17: Implement rapidfuzz entity matching
- **Type:** feature
- **Priority:** P1
- **Description:** Build entity matching engine in `core/scoring.py` using rapidfuzz. Matching priority: exact string match > fuzzy ratio > co-occurrence in text.
- **Acceptance Criteria:**
  - `core/scoring.py` defines `match_entity(query, candidates)` function
  - Exact match returns confidence=1.0
  - Fuzzy match uses rapidfuzz.fuzz.ratio() with threshold >= 80
  - Co-occurrence match checks if query appears in candidate text
  - Returns tuple: (matched_candidate, confidence_score, match_type)
  - Tests in `tests/test_scoring.py` verify all three match types
- **Dependencies:** M0-T02
- **Estimated Effort:** S
- **Status:** Complete

### M3-T18: Build equal-weight scoring algorithm
- **Type:** feature
- **Priority:** P1
- **Description:** Implement deterministic scoring: +20 points per intelligence signal, maximum 100. No AI/ML weighting. Signals: NIH funding, NSF grants, SEC filings, OpenAlex citations, arXiv papers, OpenCorporates data.
- **Acceptance Criteria:**
  - `core/scoring.py` defines `score_patent(record, signals)` function
  - Each signal contributes exactly +20 if present
  - Maximum score capped at 100 (5+ signals still = 100)
  - Score breakdown visible: "Score: 60 (NIH, NSF, OpenAlex)"
  - No randomness, no ML model, no neural network
  - Tests verify scoring math: 0 signals=0, 3 signals=60, 5 signals=100, 10 signals=100
- **Dependencies:** M3-T17
- **Estimated Effort:** S
- **Status:** Complete

### M3-T19: Create IntelligenceClient for external sources
- **Type:** feature
- **Priority:** P1
- **Description:** Build `clients/intelligence.py` with async clients for NIH RePORTER, NSF Award Search, SEC EDGAR, OpenAlex, arXiv, OpenCorporates. Mock mode for development.
- **Acceptance Criteria:**
  - `IntelligenceClient` class with methods: `search_nih()`, `search_nsf()`, `search_sec()`, `search_openalex()`, `search_arxiv()`, `search_opencorporates()`
  - Each returns list of CrossReference instances
  - Mock responses for offline development
  - Rate limiting applied (shared TokenBucket)
  - Tests in `tests/test_intelligence.py` verify mock responses
- **Dependencies:** M0-T04, M3-T18
- **Estimated Effort:** M
- **Status:** Complete

### M3-T20: Display intelligence signals in InfoTab
- **Type:** feature
- **Priority:** P1
- **Description:** Update InfoTab to show cross-reference intelligence signals with confidence percentages. Display as colored badges or text indicators.
- **Acceptance Criteria:**
  - InfoTab shows "Intelligence Signals" section when signals exist
  - Each signal displayed: source name, confidence %, URL (if available)
  - Format: "[green]●[/green] NIH: 95%" or similar
  - No signals: section hidden or shows "No external signals found."
  - Updates dynamically when patent selection changes
- **Dependencies:** M3-T19, M1-T09
- **Estimated Effort:** XS
- **Status:** Complete

---

## Milestone 4: Collections, Export & Reader Mode (COMPLETED)

### M4-T21: Add SQLite collections table with JSON serialization
- **Type:** feature
- **Priority:** P1
- **Description:** Extend CacheDatabase with collections table. Store saved patents as JSON blobs. Support add, list, clear operations.
- **Acceptance Criteria:**
  - `collections` table with fields: id (auto), patent_data (JSON), saved_at (timestamp), collection_name (default "default")
  - `save_to_collection(record, collection="default")` method
  - `get_collection(collection="default")` returns list[PatentRecord]
  - `clear_collection(collection="default")` removes all entries
  - `get_all_collections()` returns list of collection names
  - JSON serialization uses `record.to_dict()`
  - Tests verify save, retrieve, clear operations
- **Dependencies:** M0-T03
- **Estimated Effort:** S
- **Status:** Complete

### M4-T22: Implement export formatters (CSV, JSON, BibTeX, Markdown, PDF)
- **Type:** feature
- **Priority:** P1
- **Description:** Create `cli/export.py` with formatters for all five export formats. PDF uses fpdf2. All others use stdlib or minimal dependencies.
- **Acceptance Criteria:**
  - `export_csv(records, filepath)` writes RFC 4180 compliant CSV
  - `export_json(records, filepath)` writes pretty-printed JSON array
  - `export_bibtex(records, filepath)` writes BibTeX entries with @patent type
  - `export_markdown(records, filepath)` writes Markdown table + details
  - `export_pdf(records, filepath)` uses fpdf2, includes title, abstract, metadata
  - All formatters accept `list[PatentRecord]` and `pathlib.Path`
  - Dry error messages on failure: "ERR: Export failed: {reason}"
  - Tests in `tests/test_export.py` verify all 5 formats
- **Dependencies:** M4-T21
- **Estimated Effort:** M
- **Status:** Complete

### M4-T23: Add typer subcommand: recon export --format
- **Type:** feature
- **Priority:** P1
- **Description:** Wire export formatters into CLI. `recon export --format <format>` reads from default collection and writes to file.
- **Acceptance Criteria:**
  - `cli/main.py` has `export` command with `--format` option
  - Supported formats: csv, json, bibtex, markdown, pdf (case-insensitive)
  - Default output filename: `collection_export.<ext>` in current directory
  - `--output` flag for custom filepath
  - Reads from default collection via `CacheDatabase.get_collection()`
  - Empty collection: "ERR: Collection is empty. Save patents with 's' in TUI."
  - Success message: "Exported N patents to <filepath>"
- **Dependencies:** M4-T22
- **Estimated Effort:** XS
- **Status:** Complete

### M4-T24: Bind 's' hotkey to save current patent to collection
- **Type:** feature
- **Priority:** P1
- **Description:** Add `action_save_collection()` to SearchScreen. Pressing 's' saves the currently highlighted patent to the default collection.
- **Acceptance Criteria:**
  - `SearchScreen.BINDINGS` includes `("s", "save_collection", "Save to Collection")`
  - `action_save_collection()` gets highlighted patent via `result_list.highlighted_child`
  - Calls `CacheDatabase.save_to_collection(item.record)`
  - Shows notification: "Saved US1234567 to collection."
  - No-op if no patent selected (no crash)
  - Tests verify save action
- **Dependencies:** M4-T21, M2-T15
- **Estimated Effort:** XS
- **Status:** Complete

### M4-T25: Create ReaderModeScreen for distraction-free reading
- **Type:** feature
- **Priority:** P1
- **Description:** Build full-screen reader mode activated by 'r' hotkey. Shows patent abstract and claims in a clean, chrome-free interface. No Header, no Footer, no borders.
- **Acceptance Criteria:**
  - `ReaderModeScreen` class extends `Screen` (not ModalScreen)
  - `compose()` yields only a scrollable `Vertical` with `Static` content
  - NO `Header()` or `Footer()` widgets (constitution: hide all chrome)
  - Content: Title, Abstract, full Claims text
  - Keyboard: `q` quit, `j/k` scroll, `Escape` return to search
  - Minimal status line at bottom (optional): "Reader Mode | q: quit | j/k: scroll"
  - Activated from SearchScreen via `action_reader_mode()`
  - Tests verify screen composition and bindings
- **Dependencies:** M1-T10, M4-T24
- **Estimated Effort:** S
- **Status:** Complete

---

## Milestone 5: v0.2.0 Live API Integration (COMPLETED)

### M5-T26: Create core/config.py for API key management
- **Type:** feature
- **Priority:** P0
- **Description:** Build configuration system that stores API keys in `~/.config/recon/config.toml` with 0600 permissions. Support USPTO, EPO, Lens keys.
- **Acceptance Criteria:**
  - `core/config.py` defines `Config` class with fields: uspto_api_key, epo_consumer_key, epo_consumer_secret, lens_api_key
  - Config file path: `~/.config/recon/config.toml` (XDG compliant)
  - File permissions set to 0o600 on creation (owner read/write only)
  - `load()` reads from TOML file, `save()` writes to TOML file
  - `get_api_key(source)` returns key for given source name
  - No environment variables for secrets (constitution: avoid /proc leakage)
  - Tests verify load/save roundtrip
- **Dependencies:** None
- **Estimated Effort:** S
- **Status:** Complete

### M5-T27: Implement USPTO live API client
- **Type:** feature
- **Priority:** P0
- **Description:** Replace USPTO mock with live API calls to `https://api.uspto.gov/api/v1/`. Use X-API-KEY header authentication. Respect 24% rate limit headroom (76 req/min for 100/min limit).
- **Acceptance Criteria:**
  - `USPTOClient.search()` makes real HTTP request to USPTO API
  - Auth via `headers = {"X-API-KEY": config.uspto_api_key}`
  - Parses JSON response and maps to PatentRecord fields
  - Rate limiting: TokenBucket with 76 tokens/minute
  - Graceful fallback to mock data if API key missing or request fails
  - Error voice: "ERR: USPTO API failed: {status_code} {reason}"
  - Tests use pytest-httpx or VCR.py for recorded responses
- **Dependencies:** M5-T26, M0-T04
- **Estimated Effort:** M
- **Status:** Complete

### M5-T28: Implement WIPO live API client
- **Type:** feature
- **Priority:** P0
- **Description:** Replace WIPO mock with live PATENTSCOPE API calls. No authentication required. Respect rate limits.
- **Acceptance Criteria:**
  - `WIPOClient.search()` makes real HTTP request to WIPO PATENTSCOPE
  - No auth headers needed
  - Parses response format (likely XML or JSON)
  - Maps to PatentRecord with source_api="WIPO"
  - Rate limiting: 76 requests/day (conservative for no-auth API)
  - Graceful error handling with dry voice
  - Tests with mocked responses
- **Dependencies:** M0-T04
- **Estimated Effort:** M
- **Status:** Complete

### M5-T29: Integrate search_results cache with 30-day TTL
- **Type:** feature
- **Priority:** P0
- **Description:** Update cache layer to store live search results. Check cache before hitting APIs. Write results to cache after successful fetch.
- **Acceptance Criteria:**
  - `search_all()` checks cache via `cache.get_search_results(query_hash)` before API calls
  - Cache hit: returns cached results immediately (<100ms)
  - Cache miss: calls APIs, then `cache.save_search_results(query_hash, results)`
  - TTL: 30 days from `saved_at` timestamp
  - Cache invalidation: auto-expired on read, manual clear via `recon config` (optional)
  - SHA256(query_string + limit + sources) as cache key
  - Tests verify cache hit/miss behavior
- **Dependencies:** M0-T03, M5-T27, M5-T28
- **Estimated Effort:** S
- **Status:** Complete

### M5-T30: Add CLI commands: recon config set/show
- **Type:** feature
- **Priority:** P0
- **Description:** Wire config system into CLI. `recon config set --uspto-key XXX` stores keys. `recon config show` displays masked keys.
- **Acceptance Criteria:**
  - `recon config show` displays all configured keys (masked: ****)
  - `recon config set --uspto-key KEY` stores USPTO key
  - `recon config set --epo-key KEY --epo-secret SECRET` stores EPO credentials
  - `recon config set --lens-key KEY` stores Lens key
  - Validates key format (non-empty, reasonable length)
  - Creates config directory if not exists
  - Sets 0600 permissions on config file
  - Tests verify set/show roundtrip
- **Dependencies:** M5-T26
- **Estimated Effort:** XS
- **Status:** Complete

### M5-T31: Fix AsyncClient singleton for connection reuse
- **Type:** bug
- **Priority:** P1
- **Description:** CRITICAL: Creating new httpx.AsyncClient per search wastes connections. Refactor to shared singleton instance.
- **Acceptance Criteria:**
  - `BaseClient` uses class-level `_shared_client: httpx.AsyncClient | None = None`
  - `get_client()` returns existing instance or creates new one
  - AsyncClient reused across all API calls in a session
  - Connection pooling enabled (httpx default)
  - No memory leaks (client closed on app exit if needed)
  - Tests verify singleton behavior
- **Dependencies:** M0-T04
- **Estimated Effort:** XS
- **Status:** Complete

### M5-T32: Fix test mock signatures for headers parameter
- **Type:** bug
- **Priority:** P1
- **Description:** Tests fail because mock_get does not accept `headers` kwarg that real `get_with_backoff()` passes.
- **Acceptance Criteria:**
  - `mock_get` signature updated: `async def mock_get(self, url, params=None, headers=None, max_retries=4)`
  - Or use `**kwargs` to accept any parameters
  - All tests in `tests/test_integration_new.py` pass
  - All tests in `tests/test_patent_apis.py` pass
  - Full suite: 37/37 passing
- **Dependencies:** M5-T27
- **Estimated Effort:** XS
- **Status:** Complete

---

## Milestone 6: TUI Polish & Constitution Verification (COMPLETED)

### M6-T33: Audit all error states for dry, actionable voice
- **Type:** chore
- **Priority:** P1
- **Description:** Constitution T032: Review every `except` block in codebase. Ensure error messages start with "ERR:", are actionable, and never show stacktraces in standard output.
- **Acceptance Criteria:**
  - All error `print()` statements start with "ERR: "
  - No generic "Something went wrong" messages
  - No `except Exception: pass` blocks that swallow errors silently
  - Stacktraces only in debug/log mode, never in user-facing output
  - Error messages suggest next action: "ERR: USPTO API rate limited. Wait 60s or reduce query complexity."
  - grep commands confirm compliance (documented in audit log)
- **Dependencies:** All previous
- **Estimated Effort:** S
- **Status:** Complete

### M6-T34: Verify zero AI components in codebase
- **Type:** chore
- **Priority:** P1
- **Description:** Constitution T033: Audit codebase for any AI/ML libraries, neural networks, random weighting, or non-deterministic algorithms. Confirm 100% deterministic operation.
- **Acceptance Criteria:**
  - No imports from: openai, anthropic, transformers, torch, tensorflow, sklearn, numpy (unless justified)
  - Scoring uses fixed weights (+20 per signal), never learned weights
  - No `random` module usage for business logic (ok for test data)
  - No cloud AI API calls (OpenAI, Claude, Gemini, etc.)
  - Matching uses rapidfuzz (deterministic string similarity), not embeddings
  - Audit log documents verification commands and results
- **Dependencies:** All previous
- **Estimated Effort:** XS
- **Status:** Complete

### M6-T35: Remove Header/Footer from ReaderModeScreen
- **Type:** bug
- **Priority:** P1
- **Description:** ReaderModeScreen still shows Header and Footer widgets. Constitution requires "hides all chrome" for reader mode.
- **Acceptance Criteria:**
  - `ReaderModeScreen.compose()` yields NO `Header()` widget
  - `ReaderModeScreen.compose()` yields NO `Footer()` widget
  - Only content widget (Vertical + Static) and optional minimal status line
  - Full-width, no borders, no chrome
  - Visual verification: screenshot or description confirms clean layout
- **Dependencies:** M4-T25
- **Estimated Effort:** XS
- **Status:** Complete

### M6-T36: Add missing keyboard shortcuts
- **Type:** feature
- **Priority:** P1
- **Description:** Add keyboard shortcuts from spec that were missing: 'e' export, 'd' download, '/' focus search, '?' toggle help overlay.
- **Acceptance Criteria:**
  - `("e", "export_collection", "Export Collection")` in BINDINGS
  - `("d", "download_patent", "Download Patent")` in BINDINGS
  - `("/", "focus_search", "Focus Search")` in BINDINGS
  - `("?", "show_help", "Help")` in BINDINGS
  - `action_export_collection()` calls export function
  - `action_download_patent()` shows "Download queued for {id}"
  - `action_focus_search()` moves focus to search input
  - `action_show_help()` toggles inline help overlay (Static, NOT ModalScreen)
  - Tests verify all new bindings
- **Dependencies:** M4-T24, M6-T35
- **Estimated Effort:** S
- **Status:** Complete

### M6-T37: Implement inline help overlay (non-modal)
- **Type:** feature
- **Priority:** P1
- **Description:** Constitution: no modal dialogs. Help must be an inline Static widget that overlays the screen content, toggled with '?' key.
- **Acceptance Criteria:**
  - Help overlay is `Static` widget, NOT `ModalScreen`
  - Positioned fixed over content (CSS: layer, dock, or overlay)
  - Semi-transparent or bordered to distinguish from content
  - Shows all keyboard shortcuts in organized sections (Navigation, Collection, Search, Reader)
  - Toggle: '?' shows, '?' or Escape hides
  - Hidden by default
  - Does not block interaction with underlying content when visible (optional: or blocks but stays inline)
  - Tests verify toggle behavior
- **Dependencies:** M6-T36
- **Estimated Effort:** S
- **Status:** Complete

---

## Milestone 7: Bugfix & Verification (COMPLETED)

### M7-T38: Fix screens.py method name mismatch (get_all_records -> get_collection)
- **Type:** bug
- **Priority:** P0
- **Description:** `action_export_collection()` calls `db.get_all_records()` which does not exist. Correct method is `db.get_collection()`.
- **Acceptance Criteria:**
  - `tui/screens.py` line ~159 uses `db.get_collection()` not `db.get_all_records()`
  - TUI export hotkey 'e' works without AttributeError
  - Tests pass after fix
- **Dependencies:** M6-T36
- **Estimated Effort:** XS
- **Status:** Complete

### M7-T39: Fix screens.py import error (export_json -> export_records)
- **Type:** bug
- **Priority:** P0
- **Description:** `action_export_collection()` imports `export_json` from `cli.export` which does not exist. Correct import is `export_records` or similar.
- **Acceptance Criteria:**
  - `tui/screens.py` line ~156 imports correct function name from `cli.export`
  - Import matches actual function defined in `cli/export.py`
  - No ImportError on TUI startup
  - Tests pass after fix
- **Dependencies:** M7-T38
- **Estimated Effort:** XS
- **Status:** Complete

### M7-T40: Add CLI argument support to recon search
- **Type:** feature
- **Priority:** P1
- **Description:** `recon search "query"` should work as one-liner CLI mode, not just TUI mode. When query argument provided, show rich table output and exit.
- **Acceptance Criteria:**
  - `recon search "solid state battery"` executes search and prints table
  - Uses `rich` table for formatted CLI output (rich is already installed via textual)
  - Results auto-saved to default collection
  - No TUI launched when query argument provided
  - `recon search` (no args) still opens TUI
  - Tests verify both modes
- **Dependencies:** M1-T11
- **Estimated Effort:** S
- **Status:** Complete

### M7-T41: Final integration test and documentation
- **Type:** chore
- **Priority:** P1
- **Description:** Run full end-to-end test: CLI search, export, config, TUI navigation. Update tasks.md to mark all items complete. Verify 37/37 tests passing.
- **Acceptance Criteria:**
  - `recon search "solid state battery"` shows 3 patents in table
  - `recon export --format json` creates valid JSON file
  - `recon config show` displays masked keys
  - `recon search` opens TUI, arrow keys work, q quits
  - `pytest -xvs` shows 37 passed, 0 failed
  - `tasks.md` has all tasks marked complete
  - Git commit with message: "feat: v0.2.0 - Live Patent API Integration"
- **Dependencies:** All previous
- **Estimated Effort:** S
- **Status:** Complete

---

## Milestone 8: v0.3.0 - EPO OAuth 2.0 & Enhanced APIs (PLANNED)

### M8-T42: Implement EPO OAuth 2.0 client with token refresh
- **Type:** feature
- **Priority:** P1
- **Description:** Build EPO Open Patent Services (OPS) client with full OAuth 2.0 flow. Handle access token acquisition, storage, and automatic refresh when expired.
- **Acceptance Criteria:**
  - `EPOClient` implements OAuth 2.0 client credentials flow
  - Token endpoint: `https://ops.epo.org/3.2/auth/accesstoken`
  - Uses `epo_consumer_key` and `epo_consumer_secret` from config
  - Access token cached in memory, persisted optional
  - Automatic token refresh on 401 response
  - Token expiry handling (default 20 minutes)
  - Falls back to mock data if credentials missing
  - Tests mock token endpoint and API calls
- **Dependencies:** M5-T26, M5-T31
- **Estimated Effort:** M
- **Status:** Not Started

### M8-T43: Implement Google Patents unofficial scraper
- **Type:** feature
- **Priority:** P2
- **Description:** Build Google Patents client using unofficial scraping or hidden API endpoints. Fragile by nature, must handle structural changes gracefully.
- **Acceptance Criteria:**
  - `GooglePatentsClient.search()` fetches from patents.google.com
  - Parses HTML or uses internal JSON endpoints
  - Graceful degradation: if structure changes, log warning and return []
  - Rate limiting: conservative (10 req/min) to avoid blocks
  - User-Agent rotation optional
  - Tests with mocked HTML responses
- **Dependencies:** M5-T31
- **Estimated Effort:** M
- **Status:** Not Started

### M8-T44: Implement Lens.org API client
- **Type:** feature
- **Priority:** P2
- **Description:** Build Lens.org API client for academic/research-focused patent search. Requires API key from config.
- **Acceptance Criteria:**
  - `LensClient.search()` calls `https://api.lens.org/scholarly/search`
  - Auth via `Authorization: Bearer {lens_api_key}`
  - Supports advanced query syntax (Lens query language)
  - Returns PatentRecord with academic metadata (citations, scholarly works)
  - Rate limiting: 1000/day (Lens free tier)
  - Tests with mocked responses
- **Dependencies:** M5-T26, M5-T31
- **Estimated Effort:** S
- **Status:** Not Started

### M8-T45: Add source filtering to search queries
- **Type:** feature
- **Priority:** P1
- **Description:** Allow users to specify which APIs to query. `--source uspto,wipo` or interactive toggles in TUI.
- **Acceptance Criteria:**
  - CLI: `recon search "query" --source uspto,wipo`
  - TUI: Checkboxes or toggles for each source in search screen
  - `search_all()` accepts `sources=["uspto", "wipo"]` parameter
  - Default: all available sources
  - Invalid source: "ERR: Unknown source 'foo'. Available: uspto, epo, wipo, google, lens"
  - Tests verify filtering behavior
- **Dependencies:** M8-T42, M8-T43, M8-T44
- **Estimated Effort:** S
- **Status:** Not Started

---

## Milestone 9: v0.3.0 - Non-English Patent Support (PLANNED)

### M9-T46: Integrate Ollama client for local translation
- **Type:** feature
- **Priority:** P2
- **Description:** Add optional local AI translation via Ollama + DeepSeek 7B. Constitution: AI must be opt-in, never default. Requires user to explicitly enable and have Ollama running locally.
- **Acceptance Criteria:**
  - `clients/translation.py` defines `OllamaClient` class
  - Connects to `http://localhost:11434/api/generate`
  - Model: `deepseek-r1:7b` or user-configurable
  - Translates patent abstracts and claims from CN/JP/KR to English
  - AI toggle in config: `ai_translation = false` by default
  - If toggle off or Ollama unavailable, shows original text with "[original language]" badge
  - No new dependencies: uses stdlib `urllib` or `httpx` (already installed)
  - Tests mock Ollama API responses
- **Dependencies:** M5-T26
- **Estimated Effort:** M
- **Status:** Not Started

### M9-T47: Add language detection and original text display
- **Type:** feature
- **Priority:** P2
- **Description:** Detect patent language from metadata or content. Display original text alongside translation. Support CN, JP, KR, DE, FR patent sources.
- **Acceptance Criteria:**
  - `core/translation.py` defines `detect_language(text) -> str` (ISO 639-1 code)
  - Simple heuristic: character ranges for CJK, common words for European
  - PatentRecord gets `original_language` field
  - InfoTab shows "[Original: Chinese]" badge when language != English
  - Toggle in reader mode: `t` to switch original/translated
  - Tests verify detection accuracy >= 80%
- **Dependencies:** M9-T46
- **Estimated Effort:** S
- **Status:** Not Started

### M9-T48: Cache translated results
- **Type:** feature
- **Priority:** P2
- **Description:** Store translations in SQLite cache to avoid repeated Ollama calls. TTL: 90 days (translations do not change).
- **Acceptance Criteria:**
  - `translations` table: id, patent_id, language, translated_text, created_at
  - Check cache before calling Ollama
  - Cache key: SHA256(patent_id + target_language + model_version)
  - TTL: 90 days
  - Manual clear command: `recon config --clear-translations`
  - Tests verify cache hit/miss
- **Dependencies:** M9-T46, M0-T03
- **Estimated Effort:** XS
- **Status:** Not Started

---

## Milestone 10: v0.3.0 - Citation Graph Visualization (PLANNED)

### M10-T49: Fetch forward and backward citations
- **Type:** feature
- **Priority:** P2
- **Description:** Extend patent clients to fetch citation data. Backward citations (prior art cited by this patent) and forward citations (patents that cite this one).
- **Acceptance Criteria:**
  - `PatentRecord` gets `backward_citations` and `forward_citations` fields (list[str] of patent IDs)
  - USPTO client fetches citations from Patent Public Search API
  - EPO client fetches from OPS citation endpoint
  - WIPO includes citations in existing response if available
  - Lazy loading: citations fetched only when requested (not on initial search)
  - Tests verify citation parsing
- **Dependencies:** M8-T42
- **Estimated Effort:** M
- **Status:** Not Started

### M10-T50: Build ASCII/Unicode citation tree widget
- **Type:** feature
- **Priority:** P2
- **Description:** Create `CitationGraph` widget that renders patent citation network as a tree using Unicode box-drawing characters. No external graph libraries.
- **Acceptance Criteria:**
  - `tui/widgets/citation_graph.py` defines `CitationGraph(Static)`
  - Renders tree: root patent at top, backward citations below, forward citations above
  - Uses Unicode box-drawing: `├──`, `└──`, `│`
  - Click/keyboard navigation to expand/collapse branches
  - Color coding: green = forward (newer), blue = backward (older)
  - Max depth: 2 levels (configurable)
  - "No citations found." message when empty
  - Tests verify tree rendering
- **Dependencies:** M10-T49
- **Estimated Effort:** M
- **Status:** Not Started

### M10-T51: Add 'c' hotkey for citation view
- **Type:** feature
- **Priority:** P2
- **Description:** Bind 'c' key in SearchScreen to open citation graph for currently selected patent.
- **Acceptance Criteria:**
  - `("c", "show_citations", "Show Citations")` in BINDINGS
  - `action_show_citations()` pushes screen with CitationGraph widget
  - Screen title: "Citation Graph: US1234567"
  - 'q' or Escape returns to SearchScreen
  - Tests verify binding and screen transition
- **Dependencies:** M10-T50
- **Estimated Effort:** XS
- **Status:** Not Started

---

## Milestone 11: Phase C - Advanced Testing (PLANNED)

### M11-T52: Implement cache validation test suite
- **Type:** chore
- **Priority:** P1
- **Description:** Create `tests/test_cache_validation.py` with 6 tests: TTL enforcement, append-only citations, corruption recovery, cache size limits, concurrent access, eviction policy.
- **Acceptance Criteria:**
  - Test: TTL enforced (expired entries not returned)
  - Test: Append-only citations (new citations added, old preserved)
  - Test: Corruption recovery (malformed JSON handled gracefully)
  - Test: Cache size limit (LRU eviction when max size reached)
  - Test: Concurrent access (thread-safe reads/writes)
  - Test: Cache hit ratio >= 80% for repeated queries
  - All 6 tests pass
- **Dependencies:** M0-T03
- **Estimated Effort:** M
- **Status:** Not Started

### M11-T53: Implement performance benchmark suite
- **Type:** chore
- **Priority:** P1
- **Description:** Create `tests/test_performance.py` with 6 benchmarks: SC-001 (<3s search), SC-002 (<100ms navigation), memory usage, CPU usage, cold start time, large result set handling.
- **Acceptance Criteria:**
  - Benchmark: Search completes in <3 seconds (cold cache, 5 sources)
  - Benchmark: Tab switching <100ms (warm cache)
  - Benchmark: Memory usage <100MB for 1000 patents in memory
  - Benchmark: CPU usage <50% during search
  - Benchmark: Cold start (app launch to first paint) <1s
  - Benchmark: 1000 result list scrolls at 60fps
  - Uses `psutil` for resource monitoring (add to test deps)
  - Results stored in `.benchmarks/` directory
- **Dependencies:** M1-T08, M2-T14
- **Estimated Effort:** M
- **Status:** Not Started

### M11-T54: Implement error handling audit suite
- **Type:** chore
- **Priority:** P1
- **Description:** Create `tests/test_error_handling.py` with 10 scenarios verifying dry, actionable error voice. Test network failures, API errors, malformed data, disk full, permission denied, etc.
- **Acceptance Criteria:**
  - Test: Network timeout -> "ERR: Connection timed out. Check internet or try again in 30s."
  - Test: API 500 error -> "ERR: USPTO server error. Retry in 60s or try WIPO source."
  - Test: Malformed JSON -> "ERR: Invalid response from API. Report issue with query: '...'"
  - Test: Disk full -> "ERR: Disk full. Free space or change export directory."
  - Test: Permission denied -> "ERR: Permission denied. Check file permissions or run as owner."
  - Test: Rate limited -> "ERR: Rate limited. Wait 60s or reduce query frequency."
  - Test: Invalid API key -> "ERR: Invalid USPTO key. Run 'recon config set --uspto-key XXX'."
  - Test: Empty result -> "No patents found. Broaden query or check spelling."
  - Test: Cache corruption -> "ERR: Cache corrupted. Clearing and retrying..."
  - Test: Memory exhausted -> "ERR: Out of memory. Reduce result limit with --limit."
  - All 10 tests pass
  - No generic "Something went wrong" messages anywhere
- **Dependencies:** All previous
- **Estimated Effort:** M
- **Status:** Not Started

---

## Milestone 12: Documentation & Release Prep (PLANNED)

### M12-T55: Write comprehensive README.md
- **Type:** docs
- **Priority:** P2
- **Description:** Create production-quality README with badges, hero description, features, install instructions, keyboard shortcuts, API key setup, and contributing guidelines.
- **Acceptance Criteria:**
  - Badge row: build status, license (MIT), version, Python 3.12+
  - Hero: "Terminal-native patent research for technology builders"
  - 10 concrete features (not vague adjectives)
  - Install: `pip install recon` or `pip install -e .` from source
  - Quick start: 5 commands to first search
  - Keyboard shortcuts table (all 15+ shortcuts)
  - API key setup guide (USPTO, EPO, Lens links)
  - Contributing section with constitution reference
  - License: MIT
- **Dependencies:** All previous
- **Estimated Effort:** S
- **Status:** Not Started

### M12-T56: Write CONTRIBUTING.md
- **Type:** docs
- **Priority:** P2
- **Description:** Create contributor guidelines with welcome message, code of conduct, development setup, branch naming, commit conventions, PR process, testing requirements.
- **Acceptance Criteria:**
  - Welcome message + project philosophy (10 constitutional principles)
  - Code of Conduct reference (Contributor Covenant)
  - Bug report template (pre-report checklist, required fields)
  - Feature request template (constitution impact assessment)
  - Dev setup: 7 steps, fork/update commands
  - Branch naming: feat/, fix/, chore/, docs/, test/, refactor/, perf/, security/, deps/, revert/
  - Conventional Commits with RECON-specific scopes (tui, cli, search, cache, client, core, export, docs, test, deps)
  - PR template with constitution compliance checklist
  - Definition of Done: 12-item code checklist, 4-item docs checklist
- **Dependencies:** M12-T55
- **Estimated Effort:** S
- **Status:** Not Started

### M12-T57: Write SECURITY.md
- **Type:** docs
- **Priority:** P2
- **Description:** Create security policy with vulnerability reporting process, supported versions, security controls summary, and incident response brief.
- **Acceptance Criteria:**
  - Supported versions table (v0.2.0+, v0.3.0+)
  - Vulnerability reporting: email or GitHub private advisory
  - Response timeline: acknowledge 48h, assess 7d, patch 30d
  - Security controls summary (from Security & Access Control Document)
  - Dependency vulnerability management process
  - PGP key for encrypted reports (optional)
- **Dependencies:** M12-T55
- **Estimated Effort:** XS
- **Status:** Not Started

### M12-T58: Set up GitHub Actions CI/CD
- **Type:** infra
- **Priority:** P2
- **Description:** Create `.github/workflows/ci.yml` for automated testing, linting, and security scanning on every push and PR.
- **Acceptance Criteria:**
  - Trigger: push to main, pull_request to main
  - Python matrix: 3.12, 3.13, 3.14
  - Steps: checkout, setup-python, install deps, run pytest, run mypy, run pip-audit
  - Caching: pip cache enabled
  - Badge in README reflects build status
  - Security scan: pip-audit for known CVEs in dependencies
  - Job fails if any test fails or security issue found (non-blocking for optional deps)
- **Dependencies:** M11-T52, M11-T53, M11-T54
- **Estimated Effort:** S
- **Status:** Not Started

### M12-T59: Create PyPI package and release v0.2.0
- **Type:** chore
- **Priority:** P2
- **Description:** Package RECON for PyPI distribution. Set up `python -m build`, twine upload, and GitHub release with changelog.
- **Acceptance Criteria:**
  - `pyproject.toml` has complete metadata (author, license, classifiers, keywords)
  - `python -m build` generates wheel and sdist
  - Package installs with `pip install recon`
  - `recon` command available after pip install
  - GitHub release created with release notes
  - Changelog.md with version history
  - Version bump script or documented process
- **Dependencies:** M12-T55, M12-T58
- **Estimated Effort:** S
- **Status:** Not Started

---

## Appendix A: Effort Legend

| Effort | Description | Typical Duration |
|--------|-------------|------------------|
| XS | Trivial change, single file, <10 lines | 5-15 minutes |
| S | Small feature, one module, clear scope | 1-4 hours |
| M | Medium feature, multiple files, some complexity | 4-8 hours |
| L | Large feature, cross-module, significant design | 1-3 days |
| XL | Epic, architectural change, or major integration | 3-7 days |

## Appendix B: Priority Definitions

| Priority | Response Time | Description |
|----------|---------------|-------------|
| P0 | Immediate | Blocks release, data loss, security vulnerability, crash |
| P1 | 24-48 hours | Core feature missing, significant user impact, test failure |
| P2 | 1 week | Enhancement, nice-to-have, documentation, performance |
| P3 | Backlog | Refactoring, experimental, future consideration |

## Appendix C: Ticket Type Definitions

| Type | Description | Example |
|------|-------------|---------|
| feature | New functionality | "Add EPO OAuth client" |
| bug | Fix broken behavior | "Fix TUI tab switching crash" |
| chore | Maintenance, cleanup | "Update dependencies", "Refactor cache" |
| docs | Documentation only | "Write README", "Update API docs" |
| infra | Infrastructure, CI/CD | "Set up GitHub Actions", "Configure PyPI" |

## Appendix D: Current Status Summary

| Milestone | Status | Tests | Tickets |
|-----------|--------|-------|---------|
| M0: Foundation | Complete | 8 | 5/5 |
| M1: Core Search | Complete | 6 | 6/6 |
| M2: Three-Tab Preview | Complete | 6 | 5/5 |
| M3: Cross-Reference Intelligence | Complete | 2 | 4/4 |
| M4: Collections, Export & Reader | Complete | 7 | 5/5 |
| M5: v0.2.0 Live APIs | Complete | 3 | 7/7 |
| M6: TUI Polish & Constitution | Complete | 9 | 5/5 |
| M7: Bugfix & Verification | Complete | 4 | 4/4 |
| M8: EPO OAuth & Enhanced APIs | Planned | - | 4/4 |
| M9: Non-English Support | Planned | - | 3/3 |
| M10: Citation Graph | Planned | - | 3/3 |
| M11: Phase C Advanced Testing | Planned | - | 3/3 |
| M12: Documentation & Release | Planned | - | 5/5 |

**Total: 41 completed, 22 planned = 63 tickets**
**Current test count: 37/37 passing**
**Current version: v0.2.0**
