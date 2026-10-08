# RECON Agent Guide

## 1. Product Context

RECON is a terminal-native patent research CLI/TUI.
Target users are builders, analysts, and researchers who want deterministic, source-transparent patent intelligence without browser tab fatigue.

Hard constraints:
- Python 3.12+ only.
- Keyboard-first TUI.
- Zero-AI default.
- Dry error voice: `ERR:` prefix, actionable, no stacktraces.
- Minimal external dependencies.

## 2. Current Implemented Surface

These items are reflected in the current code/tests:

- CLI search and batch search.
- TUI search, tabbed preview, keyboard shortcuts, reader mode.
- Export: JSON, CSV, BibTeX, Markdown, PDF.
- Collections: save/list/clear.
- Cache: SQLite-backed search results.
- API clients:
  - USPTO with key validation.
  - EPO with API-first flow and scraper fallback, plus token caching.
  - WIPO via scraper/client path.
- Cross-reference intelligence scoring.
- Boolean query support in search.
- Boolean footer indicator in the TUI status bar.
- EPO filing date parsing from `application-reference`.
- Changelog entries and v0.2.1 notes.

## 3. Known Remaining Work

From the design docs and current state, the likely remaining work clusters into:

### 3.1 Live API Hardening
- Verify real-key behavior for USPTO/EPO/WIPO/Lens/PatSnap/Google Patents.
- Expand integration coverage beyond mocks.
- Verify rate limit behavior under real traffic.

### 3.2 Verification Gaps
- Verify T030 intent is fully satisfied by current collection/export commands.
- Verify Phase C/advanced testing coverage meets spec targets.
- Verify error voice compliance across all public CLI paths.

### 3.3 Documentation Gap
- Produce machine-readable guidance for implementation/test/docs agents.
- Preserve decision rationale in `docs/` for future contributors.

## 4. Recommended Agent Work Plan

Use this plan when delegating implementation, testing, or docs work.

### 4.1 Docs Agent
- Read `docs/DESIGN_HISTORY.md`.
- Read extracted attachment docs under `docs/attachments-extracted/`.
- Update `README.md`, `CHANGELOG.md`, and `docs/` as needed.
- Keep requirements testable and specific.

### 4.2 Implementation Agent
- Do not change stack or framework choices without explicit approval.
- Preserve keyboard-first and zero-AI default behavior.
- Add tests alongside every new feature or bugfix.
- Follow existing error-voice conventions.

### 4.3 QA/Test Agent
- Run `pytest` before proposing fixes.
- Add regression tests for:
  - TUI tab switching
  - Boolean footer state
  - EPO date parsing fallback
  - Export formats
  - Collection CRUD

## 5. Open Decisions

- Confirm whether v0.2.1 or v0.2.0 is the next tagged release.
- Decide if further API sources need formal integration tests.
- Decide if additional docs should be generated now or deferred.
