# Feature Specification: RECON Patent Research Tool

**Feature Branch**: `001-recon-patent-tool`  
**Created**: 2026-05-12  
**Status**: Draft

## User Scenarios

### User Story 1 - Core Patent Search & Fast Terminal Navigation (P1)
Users execute patent search queries across USPTO, EPO, WIPO, Google Patents, and Lens. Results display in descending list, never dropping entries. Keyboard navigation with live preview updating instantly. Deep data fetched only on explicit demand.

**Acceptance**:
1. Valid search query → results sorted descending, displayed instantly
2. Arrow key navigation → preview updates in <100ms
3. Missing metadata → flagged as `[?]` or `UNKNOWN`

### User Story 2 - Three-Tab Preview & Image Rendering (P2)
Users toggle between Info, Claims, and Image tabs. Image tab renders patent figures via Kitty, iTerm2, or Sixel protocols, falling back to external viewer.

**Acceptance**:
1. Claims tab → full claims list displayed
2. Supported terminal → inline image rendered natively
3. Unsupported terminal → opens external viewer, logs actionable message

### User Story 3 - Cross-Reference Intelligence (P3)
Users view cross-referenced intelligence (NIH, NSF, SEC, OpenAlex, arXiv, OpenCorporates). Scoring uses strictly equal weights.

**Acceptance**:
1. Patent with NSF funding → NSF linkage shown with equal weighting

### User Story 4 - Collections, Export & Reader Mode (P4)
Users save patents to collections and export to PDF, Markdown, JSON, BibTeX, CSV. Reader mode for distraction-free reading.

**Acceptance**:
1. Export to CSV → cleanly formatted file saved
2. Reader mode → UI chrome hidden, focus on abstract and claims
### User Story 5 - Intelligence Synthesis & Local AI (P5)
Users trigger a synthesis mode to summarize current search results or translate technical content using local LLMs (Ollama). All AI output is explicitly sandboxed and requires user demand.

**Acceptance**:
1. 'm' key → triggers synthesis summary of visible results
2. 't' key → translates abstract/claims into target language
3. Ollama offline → actionable error explaining how to start the service

## Functional Requirements

- **FR-001**: Zero-AI default. Deterministic operation.
- **FR-002**: Transparent data presentation. No persuasion.
- **FR-003**: Equal signal weights for scoring.
- **FR-004**: Descending sort. Never silently drop entries.
- **FR-005**: Terminal-native, keyboard-first, no GUI fallback.
- **FR-006**: Speed over depth. Deep data on explicit demand only.
- **FR-007**: Flag missing/ambiguous data explicitly.
- **FR-008**: Dry, actionable error voice.
- **FR-009**: Terminal image rendering (Kitty/iTerm2/Sixel) with external viewer fallback.
- **FR-010**: Save collections. Export to PDF, Markdown, JSON, BibTeX, CSV.
- **FR-011**: Intelligence Synthesis using local LLM (Ollama).
- **FR-012**: Jurisdiction Arbitrage status visualization for patent families.

## Key Entities

- **PatentRecord**: Title, Assignee, Dates, Abstract, Claims, Image URLs, Status, Family ID
- **CrossReference**: NIH/NSF/SEC/OpenAlex/arXiv/OpenCorporates linkage
- **Collection**: User-curated set of PatentRecords

## Success Criteria

- **SC-001**: Initial search results load in <3 seconds
- **SC-002**: Keyboard navigation updates preview in <100ms
- **SC-003**: 100% of errors provide actionable resolution steps
- **SC-004**: 100% of fetched patents present in list (ranked, never removed)

## Stack

- Python 3.12+
- Textual (TUI framework)
- httpx (async HTTP)
- Pillow (image conversion)
- rapidfuzz (name matching)
- typer (CLI)
- SQLite (cache)

## Rate Limiting

- USPTO: 76/min (24% headroom)
- EPO: 3.04/sec (24% headroom)
- WIPO: 76/day (24% headroom)
- Auto-backoff on 429: 1s → 2s → 4s → 8s → graceful fail

## Cache Strategy

- Document content: cache indefinitely
- Status metadata: refresh every 30 days (TBD after prototype)
- Citations: append-only
- Family links: refresh every 30 days

## Edge Cases

- API rate limit → `ERR: Source [Lens] rate limit exceeded. Provide API key via LENS_API_KEY.`
- Unsupported image format → `[?] FORMAT UNKNOWN`, trigger fallback
- Terminal lies about image support → graceful failure, actionable error prompting fallback config
