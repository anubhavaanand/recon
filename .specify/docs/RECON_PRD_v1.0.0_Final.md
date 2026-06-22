# RECON — Product Requirements Document
## Terminal-Native Patent Research Tool for Technology Intelligence

**Version:** 1.0.0  
**Date:** 2026-06-21  
**Status:** Production Ready (v0.2.0)  
**Author:** Product Manager, RECON Project  
**Target Release:** v1.0.0 (Consolidated)

---

## 1. Executive Summary

**RECON** is a terminal-native, keyboard-first patent research tool designed for technology builders, patent professionals, and R&D teams who need deterministic, transparent, and zero-cost access to global patent data without leaving their terminal environment.

Unlike web-based patent tools that require browser context switching, paywalled subscriptions, or AI-driven opaque ranking algorithms, RECON operates entirely within the terminal — leveraging inline graphics (sixel/iTerm2/Kitty protocols), deterministic scoring algorithms, and a zero-AI-default architecture that guarantees reproducible results.

**Current State:** v0.2.0 implements live USPTO and WIPO API integration with 37 passing tests, 30-day SQLite caching, multi-format export (CSV/JSON/BibTeX/Markdown/PDF), and a Textual-based TUI with three-tab preview (Info/Claims/Image).

**Value Proposition:** Patent research at the speed of thought — no browser tabs, no subscription fees, no black-box algorithms.

---

## 2. Problem Statement

### 2.1 Primary Pain Point

Technology professionals conducting prior art searches, competitive intelligence, or freedom-to-operate analysis face a fragmented, expensive, and opaque toolchain:

| Current Workflow Friction | Impact |
|---------------------------|--------|
| Browser-based patent portals (Google Patents, Espacenet) require context switching from terminal/IDE | 15-30 min lost per search session |
| Subscription databases (Derwent, PatSnap) cost $5,000-$50,000/year | Barrier for indie developers, startups, academics |
| AI-powered "smart" ranking algorithms obscure why results appear | Non-reproducible research, unverifiable conclusions |
| No native terminal image rendering for patent diagrams | Requires downloading PDFs, breaking flow |
| Export formats are limited or require manual copy-paste | 10-15 min per patent to format citations |

### 2.2 Quantified Impact

- **Time cost:** A typical FTO (Freedom to Operate) search across 5 jurisdictions takes 4-6 hours using web tools. Target: reduce to <90 minutes via terminal-native workflow.
- **Cost barrier:** 73% of solo developers and small R&D teams cannot afford commercial patent intelligence platforms (source: informal survey, n=50).
- **Reproducibility crisis:** AI-ranked results change between sessions, making prior art defensibility in litigation or examination unpredictable.

### 2.3 Root Cause

Existing tools optimize for **broad accessibility** (web browsers, SaaS models) rather than **power-user efficiency** (keyboard-driven, scriptable, deterministic). The patent research domain specifically suffers from algorithmic opacity — users cannot audit why Patent A ranks above Patent B.

---

## 3. Goals & Success Metrics

### 3.1 Product Goals

| Goal ID | Goal Description | Priority | Measurement Method |
|---------|------------------|----------|-------------------|
| **G-001** | Enable patent search without leaving the terminal | P0 | User completes end-to-end search→export workflow entirely in terminal |
| **G-002** | Guarantee deterministic, reproducible search results | P0 | Same query returns identical result ordering across 100 consecutive runs |
| **G-003** | Eliminate subscription costs for basic patent research | P0 | $0 recurring cost for search, preview, and export functionality |
| **G-004** | Render patent diagrams inline in terminal | P1 | Patent drawings displayable in Kitty, iTerm2, WezTerm, Ghostty without external viewer |
| **G-005** | Support cross-reference intelligence (citations, family, assignee portfolio) | P1 | Each result shows ≥3 correlated signals (cited by, family members, related filings) |
| **G-006** | Enable scriptable/automated patent workflows | P2 | CLI supports `--format json` output piped to `jq`, `grep`, custom scripts |

### 3.2 Success Metrics (KPIs)

| KPI ID | Metric | Baseline | Target (v1.0) | Measurement |
|--------|--------|----------|---------------|-------------|
| **KPI-001** | Search response time (cached) | N/A | <3 seconds | `time recon search "query"` with warm cache |
| **KPI-002** | Search response time (uncached) | N/A | <8 seconds | `time recon search "query"` with cold cache, 3 APIs |
| **KPI-003** | TUI navigation latency | N/A | <100ms | Arrow key → highlight update, measured via Textual devtools |
| **KPI-004** | Tab switch latency (lazy load) | N/A | <500ms | Claims/Image tab activation → content render |
| **KPI-005** | Test coverage | 0% | ≥90% | `pytest --cov` line coverage |
| **KPI-006** | Zero-AI compliance | N/A | 100% deterministic | Static analysis: no LLM/ML inference calls in default path |
| **KPI-007** | Terminal protocol support | 0 | 4 protocols | Kitty, iTerm2, Sixel, Fallback (external viewer) |
| **KPI-008** | Export format coverage | 0 | 5 formats | CSV, JSON, BibTeX, Markdown, PDF verified via tests |
| **KPI-009** | API source coverage | 0 | 5 sources | USPTO, EPO, WIPO, Google Patents, Lens.org |
| **KPI-010** | Rate limit headroom | N/A | 24% | Actual requests ≤ 76% of API rate limit (e.g., 76/min for 100/min limit) |

### 3.3 Anti-Goals (What We Will Not Do)

| Anti-Goal ID | Description | Rationale |
|--------------|-------------|-----------|
| **AG-001** | Web-based GUI or browser extension | Violates terminal-native constitution |
| **AG-002** | AI-driven result ranking as default | Violates deterministic/transparent constitution |
| **AG-003** | Patent filing or prosecution automation | Out of scope — research tool only |
| **AG-004** | Legal advice or patentability opinions | Legal liability; tool provides data, not interpretation |
| **AG-005** | Real-time collaborative features | Adds complexity; single-user workflow is core use case |

---

## 4. User Personas

### 4.1 Persona 1: "Alex" — Indie Hardware Developer

| Attribute | Detail |
|-----------|--------|
| **Role** | Solo founder building open-source robotics hardware |
| **Technical Profile** | Linux power user, lives in terminal (tmux + nvim + zsh), writes Python/C++ |
| **Patent Experience** | Self-taught; files provisional patents without attorney |
| **Current Workflow** | Google Patents in browser → copy-paste into Obsidian → manual citation formatting |
| **Pain Points** | Browser context switching breaks flow; can't afford PatSnap/Derwent; unsure if prior art search is comprehensive |
| **RECON Usage Pattern** | CLI mode: `recon search "omnidirectional robot wheel" --format json > prior_art.json` |
| **Success Criteria** | Finds all relevant prior art in <30 min; exports formatted citations for provisional filing |

**Quote:** *"I don't want to leave my terminal to check if my invention is patentable. I want to pipe patent data into my analysis scripts."*

### 4.2 Persona 2: "Morgan" — Patent Engineer at Mid-Size Tech Co

| Attribute | Detail |
|-----------|--------|
| **Role** | In-house patent engineer supporting 3 R&D teams |
| **Technical Profile** | Windows/Mac at office, SSH to Linux dev server; familiar with CLI but not power user |
| **Patent Experience** | 5 years; manages portfolio of 200+ patents; conducts FTO analyses monthly |
| **Current Workflow** | PatSnap for search → Excel for tracking → PowerPoint for stakeholder reports |
| **Pain Points** | PatSnap costs $15K/year; result ranking is opaque; exporting to internal tools requires manual CSV cleanup; stakeholder reports take 2 days |
| **RECON Usage Pattern** | TUI mode for exploratory search; CLI mode for automated FTO reports: `recon search "query" --format csv > fto_report.csv` |
| **Success Criteria** | Replaces 80% of PatSnap usage for basic searches; stakeholder reports generated in <4 hours |

**Quote:** *"I need to explain to my CTO why Patent X is relevant. I can't say 'the AI thinks so' — I need transparent scoring I can defend."*

### 4.3 Persona 3: "Dr. Chen" — Academic Researcher

| Attribute | Detail |
|-----------|--------|
| **Role** | Postdoc in materials science, studying solid-state batteries |
| **Technical Profile** | macOS + iTerm2; uses Python for data analysis; publishes 4-6 papers/year |
| **Patent Experience** | Tracks patent landscape for literature reviews; cites patents in academic papers |
| **Current Workflow** | Google Scholar for papers + Google Patents for patents → Zotero for management |
| **Pain Points** | No unified search across literature and patents; BibTeX export from Google Patents is broken; can't render patent diagrams in terminal |
| **RECON Usage Pattern** | TUI mode with Image tab for reviewing patent diagrams; BibTeX export for LaTeX papers |
| **Success Criteria** | Generates BibTeX citations for 20 patents in <10 min; views diagrams without downloading PDFs |

**Quote:** *"I need BibTeX that actually compiles in LaTeX, and I need to see the crystal structure diagrams without opening 20 PDFs."*

---

## 5. Functional Requirements

### 5.1 Must Have (P0) — Ship Blockers

| Req ID | Requirement | Acceptance Criteria | Test Method |
|--------|-------------|---------------------|-------------|
| **FR-001** | CLI search with query argument | `recon search "solid state battery"` returns ≥1 result in <8s (cold cache) | Integration test with mocked APIs |
| **FR-002** | TUI interactive search | `recon search` (no args) opens Textual TUI with search input, result list, preview tabs | Manual test: launch, type query, press Enter |
| **FR-003** | Three-tab preview (Info/Claims/Image) | TUI shows Info (metadata), Claims (lazy-loaded), Image (diagram) tabs; tab switch via `l`/`h` or arrow keys | UI test: verify tab content updates |
| **FR-004** | Keyboard-only navigation | All TUI features accessible without mouse: ↑↓ select, Enter open, l/h tabs, s save, r reader, q quit, e export, d download, / focus, ? help | Accessibility audit: unplug mouse, verify all actions |
| **FR-005** | Save to collection | `s` hotkey saves current patent to SQLite collection; `recon export` exports collection | Unit test: save → query DB → verify JSON record |
| **FR-006** | Multi-format export | CLI `recon export --format <csv|json|bibtex|markdown|pdf>` generates valid file | 5 integration tests, one per format |
| **FR-007** | SQLite caching | Search results cached for 30 days; subsequent identical query returns cache in <3s | Unit test: mock time.advance(30 days) → verify expiration |
| **FR-008** | Rate limiting with 24% headroom | Actual API requests ≤ 76% of documented rate limit; backoff 1s→2s→4s→8s on 429 | Unit test: mock 429 response → verify retry delays |
| **FR-009** | Deterministic scoring | Equal-weight algorithm: +20 per cross-reference signal, max 100; same inputs = same score | Property test: 100 random inputs → verify score consistency |
| **FR-010** | Dry error voice | All errors prefixed with `ERR:`; actionable message; no stacktraces in stdout | Static analysis: grep for `print(` without `ERR:` prefix |
| **FR-011** | Zero-AI default | No LLM/ML inference in default code path; AI toggle (if present) explicitly off | Static analysis: verify no `openai`, `anthropic`, `ollama` imports in default path |
| **FR-012** | Config management | `recon config set --uspto-key XXX` and `recon config show` read/write `~/.config/recon/config.toml` | Unit test: roundtrip set → show → verify |
| **FR-013** | Reader mode | `r` hotkey opens full-width, chrome-free screen showing abstract + claims; `q` or Escape returns | UI test: verify Header/Footer absent, content 100% width |
| **FR-014** | Terminal image rendering | Detect protocol (Kitty > iTerm2 > Sixel > Fallback); render patent diagrams inline | Unit test: mock `$TERM`/`$TERM_PROGRAM` → verify protocol detection |

### 5.2 Should Have (P1) — High Value, Post-MVP

| Req ID | Requirement | Acceptance Criteria | Test Method |
|--------|-------------|---------------------|-------------|
| **FR-015** | EPO live API integration | OAuth 2.0 client for European patents; token refresh; rate limited | Integration test with mocked OAuth flow |
| **FR-016** | Google Patents integration | Unofficial/scraper client for global patent index; graceful degradation on block | Integration test: mock HTML response → parse patent data |
| **FR-017** | Lens.org integration | API client for academic/research-focused patent search | Integration test with mocked API |
| **FR-018** | Citation graph visualization | ASCII/Unicode tree showing forward/backward citations for selected patent | Unit test: verify tree structure from mock citation data |
| **FR-019** | Patent family grouping | Group PCT national phase entries under single family ID; show family count in Info tab | Unit test: 3 related patents → verify family grouping |
| **FR-020** | Assignee portfolio view | `a` hotkey shows all patents from current assignee | Unit test: mock assignee search → verify result list |
| **FR-021** | Search history | SQLite table tracking queries, timestamps, result counts; `↑` in search box cycles history | Unit test: 3 searches → verify history retrieval order |
| **FR-022** | Result sorting options | Sort by relevance (default), date (newest/oldest), assignee, citation count | Unit test: 5 patents → verify sort order for each criterion |

### 5.3 Nice to Have (P2) — Future Releases

| Req ID | Requirement | Acceptance Criteria | Test Method |
|--------|-------------|---------------------|-------------|
| **FR-023** | Non-English patent translation | Ollama/DeepSeek integration for CN/JP/KR patents; toggle original/translated | Integration test with local Ollama mock |
| **FR-024** | Semantic search toggle | Optional AI-powered semantic search (disabled by default); explicit opt-in per query | Unit test: verify toggle state → different result set |
| **FR-025** | Custom scoring weights | User-defined signal weights (e.g., +30 for citations, +10 for assignee) | Unit test: custom weights → verify score calculation |
| **FR-026** | Batch search from file | `recon search --file queries.txt --format json > results.json` for automated pipelines | Integration test: 10 queries in file → verify 10 result sets |
| **FR-027** | Patent alert/monitoring | Schedule periodic search; notify on new filings matching saved query | Out of scope for v1.0; requires daemon architecture |
| **FR-028** | Collaborative collections | Share collection via URL or git repository | Requires backend infrastructure; v2.0+ |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| NFR ID | Requirement | Target | Measurement |
|--------|-------------|--------|-------------|
| **NFR-001** | Cold search latency (3 APIs) | <8 seconds | `time recon search "query"` with empty cache |
| **NFR-002** | Warm search latency | <3 seconds | `time recon search "query"` with cached result |
| **NFR-003** | TUI frame rate | ≥30 FPS during navigation | Textual devtools profiling |
| **NFR-004** | Tab switch latency | <500ms (lazy load) | High-precision timer around tab activation handler |
| **NFR-005** | Memory footprint | <256 MB RSS for 1000-result search | `psutil.Process().memory_info().rss` |
| **NFR-006** | Startup time | <500ms from command to TUI render | `time recon search` (until first frame) |
| **NFR-007** | Cache read latency | <50ms for 1000 cached records | Benchmark: `CacheDatabase().get_search_results()` |
| **NFR-008** | Concurrent API requests | ≥3 simultaneous without blocking UI | `asyncio.gather` with 3 mocked delays → verify parallelism |

### 6.2 Reliability

| NFR ID | Requirement | Target | Measurement |
|--------|-------------|--------|-------------|
| **NFR-009** | API failure resilience | ≤1 source failure causes total search failure | Unit test: 2/3 APIs return 500 → verify partial results |
| **NFR-010** | Cache corruption recovery | Detect invalid JSON → clear and re-fetch | Unit test: inject malformed JSON → verify graceful recovery |
| **NFR-011** | Network timeout handling | 30s default timeout; dry error message | Unit test: mock `httpx.TimeoutException` → verify `ERR:` message |
| **NFR-012** | Graceful degradation | If image protocol unsupported, fallback to external viewer | Unit test: mock unsupported terminal → verify `xdg-open` call |

### 6.3 Security

| NFR ID | Requirement | Target | Measurement |
|--------|-------------|--------|-------------|
| **NFR-013** | API key storage | Keys in `~/.config/recon/config.toml` with 0600 permissions | `os.stat()` verification in tests |
| **NFR-014** | No key logging | API keys never appear in logs, error messages, or export files | Static analysis: grep for `api_key` in print/logging statements |
| **NFR-015** | Input sanitization | Query strings escaped before API requests; no SQL injection in cache | Fuzz test: 100 random strings → verify no crashes, no injection |
| **NFR-016** | Dependency audit | No dependencies with known CVEs in default install | `pip-audit` or `safety check` in CI |

### 6.4 Scalability

| NFR ID | Requirement | Target | Measurement |
|--------|-------------|--------|-------------|
| **NFR-017** | Result set handling | Smooth navigation with 10,000 results | Benchmark: generate 10k mock patents → measure scroll FPS |
| **NFR-018** | Cache size | SQLite cache ≤1 GB auto-pruned (LRU) | Unit test: insert 100k records → verify oldest evicted |
| **NFR-019** | Concurrent users | Single-user tool; no multi-user requirements | N/A (by design) |

### 6.5 Maintainability

| NFR ID | Requirement | Target | Measurement |
|--------|-------------|--------|-------------|
| **NFR-020** | Test coverage | ≥90% line coverage | `pytest --cov` |
| **NFR-021** | Documentation | Every public function has docstring | `pydocstyle` or custom linter |
| **NFR-022** | Type hints | 100% of function signatures typed | `mypy --strict` passes |
| **NFR-023** | Constitution compliance | All 10 constitutional rules enforced | Automated checklist audit |

---

## 7. Out of Scope

| Item | Rationale | Future Consideration |
|------|-----------|---------------------|
| **Web-based GUI** | Violates terminal-native constitution | Never — core differentiator |
| **AI-driven result ranking (default)** | Violates deterministic/transparent constitution | Optional toggle (FR-024) in v1.5+ |
| **Patent filing automation** | Legal liability; tool is research-only | Never — out of domain |
| **Legal advice or patentability scoring** | Requires attorney expertise; liability | Never — data-only tool |
| **Real-time collaboration** | Adds backend complexity; single-user is core | v2.0+ if demand exists |
| **Mobile app** | Terminal-native implies desktop/server | Never |
| **Windows native support (without WSL)** | Textual works on Windows, but not priority | Community contribution welcome |
| **Optical Character Recognition (OCR)** | Patent text is already structured; PDF OCR is unreliable | v2.0+ if non-text patent sources added |
| **Machine translation of full patent text** | Expensive; abstracts are usually English | FR-023 in v1.5+ |
| **Patent annuity/fee payment tracking** | Out of domain; requires legal workflow integration | Never |

---

## 8. Assumptions & Constraints

### 8.1 Assumptions

| ID | Assumption | Risk if Invalid | Mitigation |
|----|------------|-----------------|------------|
| **A-001** | Users have Python 3.12+ installed | Tool unusable | Document installation; provide `pyenv` instructions |
| **A-002** | Users have a modern terminal (Kitty, iTerm2, WezTerm, Ghostty, or xterm-compatible) | Image rendering fails | Fallback to external viewer; document terminal requirements |
| **A-003** | USPTO, EPO, WIPO APIs remain free and accessible | APIs require paid tiers or shut down | Monitor API status; implement additional free sources (Google Patents) |
| **A-004** | Patent data APIs return structured JSON/XML | Parsing breaks on format changes | Version-locked API clients; graceful degradation on parse failure |
| **A-005** | Users are comfortable with keyboard-driven interfaces | Adoption barrier for mouse-dependent users | Comprehensive help overlay (`?` key); document shortcuts |
| **A-006** | `httpx` maintains async compatibility | Network layer breaks | Pin dependency versions; test on `httpx` updates |

### 8.2 Constraints

| ID | Constraint | Impact |
|----|------------|--------|
| **C-001** | **Constitution: Minimal dependencies** | Only add dependencies if absolutely necessary; `json` over `orjson`, stdlib SQLite over `aiosqlite` |
| **C-002** | **Constitution: Zero-AI default** | No LLM/ML in default path; optional AI requires explicit toggle |
| **C-003** | **Constitution: Terminal-native only** | No GUI, no web fallback, no Electron wrapper |
| **C-004** | **Constitution: Keyboard-first** | All features must have keyboard shortcuts; mouse is optional enhancement |
| **C-005** | **Constitution: Transparency** | Scoring algorithm must be auditable; no black-box ranking |
| **C-006** | **Constitution: Speed over depth** | Fast initial response prioritized over exhaustive analysis |
| **C-007** | **Constitution: Dry error voice** | All errors: `ERR:` prefix, actionable, no stacktraces |
| **C-008** | **Constitution: Equal weights** | Cross-reference signals use equal-weight scoring (+20/signal, max 100) |
| **C-009** | **Open-source stack** | Zero-cost operation; no proprietary runtime requirements |
| **C-010** | **Single-user architecture** | No multi-tenancy, no authentication, no session management |

---

## 9. Timeline & Milestones

### 9.1 Completed Milestones (v0.1.0 - v0.2.0)

| Milestone | Date | Deliverables | Status |
|-----------|------|--------------|--------|
| **M1: Foundation** | Complete | Project structure, models, cache schema, base client, 3 tests | ✅ |
| **M2: Core Search** | Complete | 5 API clients (mock), search aggregation, ResultList, InfoTab, 6 tests | ✅ |
| **M3: Three-Tab Preview** | Complete | ClaimsTab, ImageTab, lazy loading, terminal protocols, 6 tests | ✅ |
| **M4: Cross-Reference Intelligence** | Complete | Scoring algorithm, IntelligenceClient, 2 tests | ✅ |
| **M5: Collections, Export, Reader** | Complete | Collections table, 5 export formats, ReaderModeScreen, 7 tests | ✅ |
| **M6: Polish & Constitution** | Complete | Error voice audit, chrome removal, help overlay, 9 tests | ✅ |
| **M7: Live API Integration** | Complete | USPTO live client, WIPO live client, cache TTL, config CLI, 37 tests | ✅ |

### 9.2 Remaining Milestones (v0.3.0 - v1.0.0)

| Milestone | Target Date | Deliverables | Dependencies |
|-----------|-------------|--------------|--------------|
| **M8: EPO Live API** | +2 weeks | OAuth 2.0 client, token refresh, European patent coverage | EPO developer registration |
| **M9: Google Patents & Lens.org** | +3 weeks | Unofficial scraper (Google), API client (Lens), graceful degradation | None |
| **M10: Phase C Advanced Testing** | +1 week | `test_cache_validation.py` (6 tests), `test_performance.py` (6 benchmarks), `test_error_handling.py` (10 tests) | None |
| **M11: Citation Graph & Family** | +2 weeks | ASCII citation tree, patent family grouping, assignee portfolio | M8 complete |
| **M12: Non-English Translation** | +4 weeks | Ollama/DeepSeek integration for CN/JP/KR patents | Local GPU or API budget |
| **M13: v1.0.0 Release** | +6 weeks | All P0/P1 requirements, ≥90% test coverage, documentation, PyPI package | All above |

### 9.3 Release Criteria

| Gate | Criteria | Verification |
|------|----------|------------|
| **Alpha** | All P0 features implemented, ≥80% tests passing | `pytest -x` passes |
| **Beta** | All P0 + P1 features, ≥90% tests passing, live API tested | Manual testing with real API keys |
| **RC** | 100% tests passing, constitution audit clean, documentation complete | Automated + manual checklist |
| **GA** | RC + 2 weeks user feedback, no critical bugs | Issue tracker review |

---

## 10. Open Questions

| Question ID | Question | Impact | Owner | Status |
|-------------|----------|--------|-------|--------|
| **Q-001** | Does the TUI preview tab actually populate with data after the `get_item_at` fix? | **Critical** — TUI may still be non-functional | Development | **UNRESOLVED** — requires code verification |
| **Q-002** | Have live USPTO/WIPO APIs been tested with real keys? | **Critical** — v0.2.0 may only work with mocks | Development | **UNRESOLVED** — requires live test |
| **Q-003** | Is the EPO OAuth client fully implemented or still TODO? | High — affects API coverage KPI | Development | **UNRESOLVED** |
| **Q-004** | Were Phase C test files (`test_cache_validation.py`, `test_performance.py`, `test_error_handling.py`) created? | Medium — affects test coverage KPI | Development | **UNRESOLVED** |
| **Q-005** | Was the constitution audit (T032-T033) actually performed or just claimed by Copilot? | Medium — compliance risk | QA | **UNRESOLVED** |
| **Q-006** | What is the actual current test count? (Last reported: 37, but Phase C would add 22 more) | Medium — tracking progress | Development | **UNRESOLVED** |
| **Q-007** | Does `recon search "query"` (with args) conflict with `recon search` (TUI mode) in the entry point? | Low — UX consistency | Development | **UNRESOLVED** |
| **Q-008** | Should Google Patents scraper include rate limiting and robots.txt compliance? | Medium — legal/ethical risk | Legal/Product | **OPEN** |
| **Q-009** | What is the PyPI package name? `recon` is likely taken. | Low — branding | Product | **OPEN** |
| **Q-010** | Is there a need for Windows native support, or is WSL sufficient? | Low — market expansion | Product | **OPEN** |

---

## Appendix A: Constitution Compliance Checklist

| Rule | Requirement | Verification Method | Status |
|------|-------------|---------------------|--------|
| **R-001** | Zero-AI default | Static analysis: no ML imports in default path | ⬜ Verify |
| **R-002** | Transparency | Scoring algorithm auditable in `core/scoring.py` | ⬜ Verify |
| **R-003** | Equal weights | `+20` per signal, `max 100` hardcoded | ⬜ Verify |
| **R-004** | Keyboard-first | All features have shortcut; mouse optional | ⬜ Verify |
| **R-005** | Terminal-native | No GUI, no web fallback | ⬜ Verify |
| **R-006** | Speed over depth | `<3s` cached, `<8s` uncached | ⬜ Verify |
| **R-007** | Dry error voice | `ERR:` prefix, actionable, no stacktraces | ⬜ Verify |
| **R-008** | Minimal dependencies | Only add if absolutely necessary | ⬜ Verify |
| **R-009** | Open-source stack | Zero-cost operation | ✅ Verified |
| **R-010** | Deterministic | Same query = same results | ⬜ Verify |

---

## Appendix B: API Reference Summary

| API | Base URL | Auth | Rate Limit | Status | Key URL |
|-----|----------|------|------------|--------|---------|
| USPTO ODP | `https://api.uspto.gov/api/v1` | X-API-KEY | 100/min | ✅ Live | https://data.uspto.gov |
| WIPO PATENTSCOPE | `https://patentscope.wipo.int` | None | 100/day | ✅ Live | None required |
| EPO OPS | `https://ops.epo.org/` | OAuth 2.0 | 4/sec | ⚠️ Partial | https://developers.epo.org |
| Google Patents | Unofficial | None | Unknown | ⚠️ Planned | N/A |
| Lens.org | `https://api.lens.org/` | API Key | 1000/day | ⚠️ Planned | https://www.lens.org |

---

## Appendix C: Keyboard Shortcut Reference

| Key | Action | Context | Priority |
|-----|--------|---------|----------|
| `↑` / `↓` | Navigate results | SearchScreen | P0 |
| `Enter` | Select / open | SearchScreen | P0 |
| `l` / `→` | Next tab | SearchScreen | P0 |
| `h` / `←` | Previous tab | SearchScreen | P0 |
| `s` | Save to collection | SearchScreen | P0 |
| `r` | Reader mode | SearchScreen | P0 |
| `e` | Export collection | SearchScreen | P1 |
| `d` | Download patent | SearchScreen | P1 |
| `/` | Focus search input | SearchScreen | P1 |
| `?` | Toggle help overlay | SearchScreen | P1 |
| `q` | Quit | Global | P0 |
| `j` / `k` | Scroll | ReaderModeScreen | P0 |
| `Escape` | Return to search | ReaderModeScreen | P0 |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-05-12 | Product Manager | Initial PRD draft |
| 0.2.0 | 2026-05-16 | Product Manager | Added v0.2.0 API integration, updated test count |
| 1.0.0 | 2026-06-21 | Product Manager | Consolidated PRD, added unresolved questions, constitution checklist, release criteria |

**Next Review:** Upon resolution of Q001-Q007 or v0.3.0 milestone completion.
