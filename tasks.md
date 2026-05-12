---
description: "Task list for RECON Patent Research Tool implementation"
---

# Tasks: RECON Patent Research Tool

**Input**: Design documents from `specs/001-recon-patent-tool/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Per the Constitution (III. Test-First), test tasks are mandatory. Tests must be written and fail before implementation begins.

**Organization**: Tasks are grouped sequentially starting with setup, followed by User Stories (P1 -> P4), and ending with final polish.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)

---

## Phase 1: Setup & Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be complete before any user story can be implemented.

- [ ] T001 [P] [Setup] Initialize Python 3.12+ project structure (`cli/`, `tui/`, `core/`, `clients/`, `storage/`).
- [ ] T002 [P] [Setup] Configure linting, formatting, and `pytest` with `pytest-asyncio`.
- [ ] T003 [Foundational] Define `PatentRecord` and `CrossReference` pydantic/dataclass entities in `core/models.py`.
- [ ] T004 [Foundational] Implement SQLite cache schema (`search_results`, `patent_details`, `collections`, `cross_references`) in `storage/cache.py`.
- [ ] T005 [Foundational] Create `httpx` base async client with auto-backoff and dry error logging (`ERR: Source [API] rate limit exceeded`) in `clients/patent_apis.py`.

**Checkpoint**: Foundation ready - US1 implementation can begin.

---

## Phase 2: User Story 1 - Core Patent Search & Fast Terminal Navigation (P1)

**Goal**: Core terminal-native search with descending sort, keyboard navigation, and <50ms cache-backed previews.

### Tests for User Story 1 (Must fail first)
- [ ] T006 [P] [US1] Write failing mock tests for USPTO, EPO, WIPO, Google Patents, and Lens search clients.
- [ ] T007 [P] [US1] Write failing Textual async pilot test for list navigation ensuring <50ms preview update.
- [ ] T008 [P] [US1] Write failing tests to assert descending sort logic strictly never drops entries.

### Implementation for User Story 1
- [ ] T009 [US1] Implement API wrappers for primary search sources in `clients/patent_apis.py`.
- [ ] T010 [US1] Build `core/search.py` using `asyncio.gather` for concurrent fetching and merging.
- [ ] T011 [US1] Implement missing data flagger mapping `None` to `[?]` or `UNKNOWN` in `PatentRecord` processing.
- [ ] T012 [P] [US1] Create `ResultList` Textual widget in `tui/widgets/result_list.py`.
- [ ] T013 [P] [US1] Create `InfoTab` Textual preview widget in `tui/widgets/info_tab.py`.
- [ ] T014 [US1] Wire up `SearchScreen` layout in `tui/screens.py`, binding keyboard events to update preview from SQLite cache.
- [ ] T015 [US1] Integrate `typer` CLI entrypoint in `cli/main.py` to launch the Textual app.

**Checkpoint**: Search executes, results populate, keyboard navigation updates the Info tab instantly.

---

## Phase 3: User Story 2 - Three-Tab Preview & Image Rendering (P2)

**Goal**: Expand preview to Info/Claims/Image tabs. Implement terminal-native image rendering with fallback.

### Tests for User Story 2 (Must fail first)
- [ ] T016 [P] [US2] Write failing tests for terminal protocol detection (Kitty/iTerm2/Sixel).
- [ ] T017 [P] [US2] Write failing tests verifying lazy-loading mechanism (`speed over depth` constraint).

### Implementation for User Story 2
- [ ] T018 [US2] Implement Textual `TabbedContent` with Info, Claims, and Image tabs in `tui/screens.py`.
- [ ] T019 [US2] Build `claims_tab.py` with an async fetcher bound to `on_tab_activated` to lazy-load claims.
- [ ] T020 [US2] Implement `Pillow` based terminal image generator in `tui/widgets/image_tab.py`.
- [ ] T021 [US2] Implement OS-level external viewer fallback for unsupported images/terminals, logging dry error.

**Checkpoint**: Tabs toggle smoothly. Claims load on-demand. Images render natively or open externally.

---

## Phase 4: User Story 3 - Cross-Reference Intelligence (P3)

**Goal**: Deterministic entity matching against NIH, NSF, SEC, OpenAlex, arXiv, OpenCorporates.

### Tests for User Story 3 (Must fail first)
- [ ] T022 [P] [US3] Write failing tests for `rapidfuzz` entity matching.
- [ ] T023 [P] [US3] Write failing tests explicitly verifying equal-weight scoring logic calculates purely `1+1=2`.

### Implementation for User Story 3
- [ ] T024 [P] [US3] Implement `clients/intelligence.py` for query execution against external datasets.
- [ ] T025 [US3] Implement deterministic entity matching algorithm in `core/scoring.py`.
- [ ] T026 [US3] Update `InfoTab` in `tui/widgets/info_tab.py` to display the transparent intelligence signals.

**Checkpoint**: Cross-referenced intelligence shows exact matching metadata and pure sum score.

---

## Phase 5: User Story 4 - Collections, Export & Reader Mode (P4)

**Goal**: Save patents to local SQLite collection, export cleanly via CLI, read securely in UI.

### Tests for User Story 4 (Must fail first)
- [ ] T027 [P] [US4] Write failing tests for CSV, JSON, BibTeX, Markdown, and PDF export integrity.

### Implementation for User Story 4
- [ ] T028 [US4] Add local Collection saving hotkey (`s`) bound to SQLite update in `tui/screens.py`.
- [ ] T029 [P] [US4] Implement formatters in `cli/export.py` (utilizing standard libs + basic formatting).
- [ ] T030 [US4] Add `typer` subcommands in `cli/main.py` for exporting collections (e.g., `recon export --format csv`).
- [ ] T031 [US4] Create `ReaderModeScreen` in `tui/screens.py` that hides left list pane for full-screen reading.

**Checkpoint**: Patents can be saved, exported from the CLI, and viewed cleanly in reader mode.

---

## Phase 6: Polish & Constitution Verification

**Purpose**: Ensure strict adherence to core principles.

- [ ] T032 [Polish] Audit all error states to guarantee dry, actionable voice without stacktraces in standard output.
- [ ] T033 [Polish] Final test pass verifying exactly zero AI components or unpredictable algorithms exist in the codebase.