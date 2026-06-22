# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## How to Update This File

**Before every release, contributors must:**

1. **Move items from `[Unreleased]` to a new version section.**
2. **Create the new version section** with format `## [X.Y.Z] - YYYY-MM-DD`.
3. **Categorize each change** under one of these headers:
   - `Added` — new features
   - `Changed` — changes to existing functionality
   - `Deprecated` — soon-to-be removed features
   - `Removed` — now-removed features
   - `Fixed` — bug fixes
   - `Security` — vulnerability fixes
4. **Write each entry as one line**, past tense, starting with a verb.
5. **Add a comparison link** in the footer for the new version.
6. **Leave `[Unreleased]` empty** after release (or with a placeholder).

**Example entry:**
```
### Fixed
- Replaced fragile `get_item_at()` with `highlighted_child` for ListView access
```

---

## [Unreleased]

### Added
- Placeholder for upcoming v0.3.0 features

### Changed
- Placeholder for upcoming v0.3.0 changes

### Deprecated
- Placeholder for upcoming v0.3.0 deprecations

### Removed
- Placeholder for upcoming v0.3.0 removals

### Fixed
- Placeholder for upcoming v0.3.0 fixes

### Security
- Placeholder for upcoming v0.3.0 security patches

## [0.2.0] - 2026-05-16

### Added
- Implemented live USPTO patent search API client with `X-API-KEY` authentication
- Implemented live WIPO PATENTSCOPE API client with no-auth public access
- Added `core/config.py` for secure API key storage in `~/.config/recon/config.toml`
- Added `recon config set` and `recon config show` CLI subcommands for key management
- Added `search_results` SQLite table with 30-day TTL cache expiration
- Added shared `httpx.AsyncClient` singleton in `clients/base.py` for connection pooling
- Added CLI table output for `recon search "query"` using `rich` (bundled with Textual)
- Added `recon export --format` subcommand with JSON, CSV, BibTeX, Markdown, and PDF support
- Added `recon search` TUI mode with interactive search interface
- Added ReaderModeScreen (`r` hotkey) for distraction-free full-width patent reading
- Added Collections system (`s` hotkey) with SQLite JSON serialization
- Added Help Overlay (`?` hotkey) as inline Static widget (non-modal)
- Added keyboard shortcuts: `e` (export), `d` (download), `/` (focus search), `?` (help)
- Added cross-reference intelligence with rapidfuzz entity matching
- Added equal-weight scoring algorithm (+20 per signal, max 100)
- Added IntelligenceClient for NIH/NSF/SEC/OpenAlex/arXiv/OpenCorporates signals
- Added terminal image protocol detection (Kitty > iTerm2 > Sixel > Fallback)
- Added Pillow-based inline image rendering with escape sequences
- Added external viewer fallback (`xdg-open`) for unsupported terminals
- Added rate limiting with 24% headroom (76/min for USPTO, 76/day for WIPO)
- Added auto-backoff strategy (1s → 2s → 4s → 8s) for 429 responses
- Added `test_cache_validation.py` with 6 tests for TTL enforcement and corruption recovery
- Added `test_performance.py` with 6 benchmarks for <3s search and <100ms navigation
- Added `test_error_handling.py` with 10 scenarios for dry error voice verification
- Added `test_tui_navigation.py` with 9 tests for keyboard shortcuts and overlay behavior

### Changed
- Refactored mock API clients in `clients/patent_apis.py` to live HTTP implementations
- Updated `storage/cache.py` to write and read live search results with expiration logic
- Updated `core/search.py` to orchestrate live API calls with cache-aside pattern
- Updated `cli/main.py` to support both TUI mode (no args) and CLI table mode (with query)
- Improved `ResultList` widget to use `highlighted_child` instead of fragile `children[index]`
- Enhanced `SearchScreen` with additional keyboard bindings and inline help overlay
- Modified `ReaderModeScreen` to remove Header/Footer for full chrome-free immersion
- Replaced `get_item_at()` calls with proper Textual `highlighted_child` API across 4 methods
- Strengthened test suite from 25 to 37 passing tests
- Updated `pyproject.toml` with `[project.scripts]` entry point for `recon` CLI command

### Fixed
- Fixed `AttributeError: 'ResultList' object has no attribute 'get_item_at'` in TUI tab switching
- Fixed import mismatch in `cli/main.py` (`search_patents` → correct function name)
- Fixed `test_integration_new.py` mock signature to accept `headers` and `**kwargs`
- Fixed `test_patent_apis.py` to mock network calls and config for isolated test runs
- Fixed `_load_active_tab()` to strip `--content-tab-` prefix from Textual tab IDs
- Fixed `action_export_collection()` method name mismatch (`get_all_records()` → `get_collection()`)
- Fixed `action_export_collection()` import error (`export_json` → `export_records`)
- Fixed bounds checking in ListView access (`0 <= index < len(children)`)

### Security
- Enforced `0600` file permissions on `~/.config/recon/config.toml` for API key storage
- Added input sanitization for search queries to prevent injection attacks
- Implemented dry error voice (`ERR:` prefix) to prevent stacktrace leakage in standard output
- Added structured JSON audit logging for API calls and cache operations

## [0.1.0] - 2026-05-12

### Added
- Initialized Python 3.12+ project structure (`cli/`, `tui/`, `core/`, `clients/`, `storage/`)
- Configured `pytest` with `pytest-asyncio` for async test support
- Defined `PatentRecord` and `CrossReference` dataclasses (stdlib only, no Pydantic)
- Implemented SQLite cache schema (`document_content`, `status_metadata`, `citations`, `family_links`)
- Created `httpx` async client with 1s→2s→4s→8s auto-backoff strategy
- Built mock clients for USPTO, EPO, WIPO, Lens, and Google Patents APIs
- Implemented search aggregation with `asyncio.gather` for concurrent fetching
- Enforced descending sort that never silently drops entries
- Added missing data flagger converting `None` to `[?]` or `UNKNOWN`
- Created `ResultList` and `InfoTab` Textual widgets for TUI
- Wired `SearchScreen` with keyboard navigation and <100ms preview updates
- Integrated `typer` CLI entrypoint (`recon search`)
- Added `TabbedContent` with Info, Claims, and Image tabs
- Implemented lazy-loaded `ClaimsTab` (fetch on tab activation only)
- Added `Collections` table with JSON serialization and `s` hotkey binding
- Added export formatters for CSV, JSON, BibTeX, Markdown, and PDF (`fpdf2`)
- Added 25 foundational tests across models, cache, search, and client modules
- Added project constitution in `.specify/docs/constitution.md`
- Added `README.md` with installation, usage, and keyboard shortcuts
- Added `CONTRIBUTING.md` with branch naming, commit conventions, and definition of done
- Added `SECURITY.md` with vulnerability reporting policy
- Added `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`
- Added GitHub Actions CI workflow for automated testing

### Changed
- Adopted k9s + ncspot hybrid aesthetic for terminal-native UI design
- Established keyboard-first navigation as primary interaction model
- Set zero-AI default with optional deterministic scoring toggle

### Fixed
- Fixed `highlighted_child` access pattern for Textual `ListView` selection
- Fixed tab ID prefix stripping in `_load_active_tab()` for Textual `TabbedContent`

[Unreleased]: https://github.com/anubhavaanand/recon/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/anubhavaanand/recon/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/anubhavaanand/recon/releases/tag/v0.1.0
