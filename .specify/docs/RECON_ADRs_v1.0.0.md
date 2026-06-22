# RECON Architecture Decision Records (ADRs)

> **Project:** RECON — Terminal-native patent research tool for technology builders
> **Repository:** `https://github.com/anubhavaanand/recon`
> **Version:** 1.0.0
> **Last Updated:** 2026-06-22

---

## ADR Index

| ID | Title | Status | Date | Impact |
|:---|:---|:---|:---|:---|
| [ADR-001](#adr-001-terminal-native-over-web-based) | Terminal-Native Over Web-Based | Accepted | 2026-05-12 | Architecture |
| [ADR-002](#adr-002-textual-over-alternative-tui-frameworks) | Textual Over Alternative TUI Frameworks | Accepted | 2026-05-12 | Framework |
| [ADR-003](#adr-003-sqlite-over-postgresql) | SQLite Over PostgreSQL | Accepted | 2026-05-12 | Database |
| [ADR-004](#adr-004-zero-ai-default-with-optional-toggles) | Zero-AI Default with Optional Toggles | Accepted | 2026-05-12 | Philosophy |
| [ADR-005](#adr-005-minimal-dependency-constitution) | Minimal Dependency Constitution | Accepted | 2026-05-12 | Dependencies |
| [ADR-006](#adr-006-asyncio-over-threading) | Asyncio Over Threading | Accepted | 2026-05-12 | Concurrency |
| [ADR-007](#adr-007-json-columns-over-normalized-schema) | JSON Columns Over Normalized Schema | Accepted | 2026-05-12 | Data Model |
| [ADR-008](#adr-008-httpx-over-requests) | httpx Over requests | Accepted | 2026-05-12 | HTTP Client |
| [ADR-009](#adr-009-single-process-over-client-server) | Single-Process Over Client-Server | Accepted | 2026-05-12 | Deployment |
| [ADR-010](#adr-010-rapidfuzz-over-ml-semantic-search) | rapidfuzz Over ML Semantic Search | Accepted | 2026-05-12 | Scoring |
| [ADR-011](#adr-011-24-percent-rate-limit-headroom) | 24% Rate Limit Headroom | Accepted | 2026-05-12 | Resilience |
| [ADR-012](#adr-012-dry-error-voice-over-stacktraces) | Dry Error Voice Over Stacktraces | Accepted | 2026-05-12 | UX |
| [ADR-013](#adr-013-inline-static-over-modal-dialogs) | Inline Static Over Modal Dialogs | Accepted | 2026-05-12 | TUI Design |
| [ADR-014](#adr-014-phase-based-git-commits) | Phase-Based Git Commits | Accepted | 2026-05-12 | Workflow |
| [ADR-015](#adr-015-kitty-iterm2-sixel-fallback-chain) | Kitty > iTerm2 > Sixel > Fallback Image Chain | Accepted | 2026-05-12 | Image Rendering |
| [ADR-016](#adr-016-stdblib-json-over-orjson) | stdlib json Over orjson | Accepted | 2026-05-12 | Serialization |
| [ADR-017](#adr-017-no-certificate-pinning) | No Certificate Pinning | Accepted | 2026-05-12 | Security |
| [ADR-018](#adr-018-no-rbac-abac-acl) | No RBAC/ABAC/ACL | Accepted | 2026-05-12 | Authorization |
| [ADR-019](#adr-019-file-based-secrets-over-environment-variables) | File-Based Secrets Over Environment Variables | Accepted | 2026-05-12 | Secrets Management |
| [ADR-020](#adr-020-no-horizontal-scaling) | No Horizontal Scaling | Accepted | 2026-05-12 | Scalability |
| [ADR-021](#adr-021-typer-over-argparse) | Typer Over argparse | Accepted | 2026-05-12 | CLI Framework |
| [ADR-022](#adr-022-fpdf2-over-reportlab) | fpdf2 Over reportlab | Accepted | 2026-05-12 | PDF Generation |
| [ADR-023](#adr-023-no-soft-deletes) | No Soft Deletes | Accepted | 2026-05-12 | Data Lifecycle |
| [ADR-024](#adr-024-sha256-query-hash-over-auto-increment-pk) | SHA256 Query Hash Over Auto-Increment PK | Accepted | 2026-05-12 | Caching |
| [ADR-025](#adr-025-concurrent-api-gather-over-sequential) | Concurrent API Gather Over Sequential | Accepted | 2026-05-12 | Search Performance |
| [ADR-026](#adr-026-lazy-loading-over-eager-fetching) | Lazy Loading Over Eager Fetching | Accepted | 2026-05-12 | TUI Performance |
| [ADR-027](#adr-027-no-docker-no-kubernetes) | No Docker, No Kubernetes | Accepted | 2026-05-12 | Infrastructure |
| [ADR-028](#adr-028-100-character-line-length) | 100-Character Line Length | Accepted | 2026-05-12 | Code Style |
| [ADR-029](#adr-029-no-alembic-versioned-sql-migrations) | No Alembic, Versioned SQL Migrations | Accepted | 2026-05-12 | Schema Management |
| [ADR-030](#adr-030-epo-oauth2-over-api-key) | EPO OAuth2 Over API Key | Accepted | 2026-05-12 | Authentication |

---

## ADR-001: Terminal-Native Over Web-Based

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead (anubhavaanand)
- **Tags:** #architecture #philosophy #terminal

### Context

Patent research tools are overwhelmingly web-based (PatentScope, Google Patents, Lens.org). Users are forced into browser tabs, JavaScript-heavy interfaces, and mouse-dependent workflows. The target user (technology builders, patent engineers, researchers) spends significant time in terminals already — running builds, managing infrastructure, reviewing code.

The core question: Should RECON be a web application (SaaS, local server + browser) or a terminal-native application?

### Decision

**RECON will be terminal-native.** No web server. No browser. No JavaScript. The entire application runs inside a terminal emulator.

### Consequences

**Positive:**
- Zero infrastructure cost — no server, no hosting, no SSL certificates
- Instant startup — no browser tab creation, no HTTP handshake
- Keyboard-first by default — every operation accessible without mouse
- Works over SSH — remote patent research on headless servers
- No frontend framework complexity — no React, no bundling, no CSS-in-JS
- Privacy by default — no analytics, no cookies, no third-party scripts
- Works offline after cache warm — SQLite is local, no network for cached results

**Negative:**
- Limited to users comfortable with terminals (acceptable: target audience)
- No mobile support (acceptable: patent research is desktop work)
- Image rendering requires terminal protocol support (Kitty/iTerm2/Sixel)
- Cannot embed rich web content (iframes, interactive charts)
- Distribution via pip instead of URL — slightly higher friction for non-developers
- Accessibility tools (screen readers) have varying TUI support

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Web app (Flask/FastAPI + browser)** | Universal access, rich UI, easy sharing | Requires server, browser dependency, mouse-centric, hosting cost | Rejected — violates privacy-first, adds infrastructure |
| **Electron desktop app** | Native feel, web tech stack | Massive bundle size, Chromium overhead, security surface | Rejected — overkill for a research tool |
| **TUI (Textual)** | Python-native, async, rich widgets, keyboard-first | Terminal-only, image rendering complexity | **Chosen** — optimal for target audience |
| **CLI-only (no TUI)** | Simplest possible, scripting-friendly | No interactive preview, no inline images | Rejected — preview is core value proposition |

---

## ADR-002: Textual Over Alternative TUI Frameworks

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #framework #tui #python

### Context

Python has several TUI frameworks: Textual, Rich (lower-level), urwid (legacy), npyscreen (abandoned), PySimpleGUI (not terminal), and cross-language options like Bubble Tea (Go), tview (Go), or blessed (Node.js). The choice of framework determines widget availability, async support, CSS-like styling, and long-term maintenance.

### Decision

**Use Textual** as the exclusive TUI framework. No other TUI library in the dependency tree.

### Consequences

**Positive:**
- CSS-like styling with `styles.css` files — familiar to web developers
- Built-in async support — `async def` event handlers natively
- Rich widget set: DataTable, Tree, TabbedContent, Markdown, Static, Input
- Active maintenance by Textualize Inc — funded, full-time team
- Large community — extensive examples, Discord support
- `highlighted_child` and `ListView` APIs for keyboard navigation
- Built-in `ModalScreen` (constitutionally prohibited but available if ever needed)

**Negative:**
- Heavy dependency (~20MB with Rich included)
- `ListView` API quirks (no `get_item_at()`, prefix tab IDs with `--content-tab-`)
- CSS specificity sometimes unpredictable
- Event bubbling can be complex for nested widgets
- Startup time slightly slower than raw curses

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Rich (lower-level)** | Lighter, faster, more control | No built-in widgets, manual layout math | Rejected — too much boilerplate for complex TUI |
| **urwid** | Mature, stable | Python 2 legacy, no async, abandoned docs | Rejected — end-of-life framework |
| **npyscreen** | Simple forms | Abandoned, no async, limited widgets | Rejected — unmaintained |
| **Bubble Tea (Go)** | Beautiful, performant | Requires Go toolchain, FFI complexity, language mismatch | Rejected — Python ecosystem preferred |
| **tview (Go)** | Fast, lightweight | Go language, no Python integration | Rejected — language mismatch |
| **Blessed (Node.js)** | Rich terminal control | Node.js dependency, not Python-native | Rejected — language mismatch |
| **Custom curses** | Zero dependencies | Massive effort, platform bugs, no async | Rejected — not feasible for MVP |

---

## ADR-003: SQLite Over PostgreSQL

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #database #storage #stdlib

### Context

Patent search results need caching to avoid repeated API calls. The cache stores: search queries (SHA256 hash as PK), patent documents (JSON), collections (JSON), citations, and metadata. The question is whether to use a local file-based database (SQLite) or a client-server database (PostgreSQL).

### Decision

**Use SQLite** as the sole database. No PostgreSQL, no MongoDB, no Redis. A single `.db` file in `~/.local/share/recon/`.

### Consequences

**Positive:**
- Zero configuration — no `CREATE DATABASE`, no users, no ports
- Single file — easy backup, copy, delete
- Stdlib-adjacent — `sqlite3` in Python standard library (no pip install)
- ACID transactions — reliable even on power loss
- WAL mode — readers don't block writers
- FTS5 extension — full-text search on tags and titles
- JSON1 extension — native JSON operations in SQLite 3.38+
- Perfect for single-user, single-process application

**Negative:**
- Single-writer bottleneck — concurrent writes serialize (acceptable: single user)
- No advanced types — arrays, enums simulated in Python (acceptable)
- No built-in replication — single point of failure (acceptable: cache is rebuildable)
- File locking issues on network drives (acceptable: local filesystem only)
- Query planner less sophisticated than PostgreSQL for complex joins

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **PostgreSQL** | Advanced types, concurrent writers, replication | Requires server process, configuration, port management | Rejected — overkill for single-user tool |
| **MongoDB** | Flexible schema, JSON-native | Requires daemon, memory-heavy, not stdlib | Rejected — document store unnecessary |
| **Redis** | In-memory speed, pub/sub | Ephemeral by default, requires server, not ACID | Rejected — cache needs persistence |
| **DuckDB** | Analytical queries, columnar | Newer, smaller community, overkill for OLTP | Rejected — analytical features not needed |
| **LevelDB/RocksDB** | Key-value, fast | No SQL interface, no JSON support | Rejected — need relational + JSON |
| **JSON files on disk** | Zero dependencies | No ACID, no indexing, corruption risk | Rejected — need transactions |

---

## ADR-004: Zero-AI Default with Optional Toggles

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #philosophy #ai #constitution

### Context

Most modern patent tools aggressively integrate AI: semantic search, LLM summarization, claim analysis, prior art matching. These features are convenient but introduce non-determinism, hallucination risk, vendor lock-in, and API costs. The target user (technology builder) needs reproducible, auditable research.

### Decision

**Zero-AI is the default.** All scoring, matching, and ranking use deterministic algorithms (rapidfuzz string matching, equal-weight scoring). AI features (translation, semantic search) are explicitly opt-in via toggles and only use local models (Ollama) or user-provided APIs.

### Consequences

**Positive:**
- Fully reproducible results — same query always returns same ranking
- No API keys for AI services required by default
- No hallucination risk in patent analysis
- Transparent scoring — user can trace why a patent ranked #1
- No vendor lock-in to OpenAI/Anthropic/Google
- Works entirely offline after initial data fetch
- Fast — no network round-trips to AI APIs

**Negative:**
- Less "intelligent" matching than semantic embeddings
- No automatic summarization of long claims
- No natural language query understanding (must use Boolean/field operators)
- Translation requires explicit opt-in and local LLM setup
- Users accustomed to ChatGPT-like interfaces may find it spartan

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **AI-first (OpenAI/Claude)** | Best matching, summaries, natural language | Non-deterministic, API costs, hallucination, vendor lock-in | Rejected — violates transparency principle |
| **Hybrid default (AI on)** | Best of both worlds | Still requires API keys, still non-deterministic | Rejected — default matters |
| **Local AI default (Ollama)** | Private, no API costs | Requires GPU/8GB RAM, slower, model management | Rejected — not zero-config |
| **Zero-AI default, optional toggles** | Deterministic, transparent, opt-in AI | Less "smart" out of the box | **Chosen** — aligns with constitution |

---

## ADR-005: Minimal Dependency Constitution

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #dependencies #philosophy #maintenance

### Context

Python dependency trees grow uncontrollably. A typical "simple" project can pull in 50+ transitive dependencies, each a potential security vulnerability, breaking change, or compatibility issue. For a tool that may run for years on a developer's machine, dependency bloat creates maintenance burden.

### Decision

**Maximum 8 direct dependencies.** Any addition requires explicit justification and constitutional amendment. Current accepted dependencies: `textual`, `httpx`, `Pillow`, `rapidfuzz`, `typer`, `fpdf2`, `tomli`/`tomli-w`.

### Consequences

**Positive:**
- Fast `pip install` — seconds not minutes
- Small attack surface — fewer CVEs to track
- Easy auditing — can read every dependency's source in an afternoon
- Long-term stability — less churn from upstream breaking changes
- Portable — works on systems with restricted package managers
- Fast CI — minimal environment setup

**Negative:**
- Must reimplement some features instead of importing libraries
- Cannot use convenience packages (e.g., `pydantic`, `sqlalchemy`, `click`)
- JSON parsing slower than `orjson` (acceptable for <100KB responses)
- No ORM — manual SQL construction
- No advanced data validation — manual checks in Python

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Standard Python packaging (unlimited deps)** | Maximum convenience, reuse everything | Dependency hell, security surface, slow installs | Rejected — violates minimalism |
| **8-direct-dep limit with careful curation** | Balanced power and simplicity | Requires discipline, occasional reinvention | **Chosen** — sustainable long-term |
| **Zero dependencies (stdlib only)** | Purest minimalism | Would require reimplementing HTTP, image processing, TUI | Rejected — not feasible for MVP |

---

## ADR-006: Asyncio Over Threading

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #concurrency #async #performance

### Context

RECON makes multiple HTTP requests to patent APIs (USPTO, WIPO, EPO, Google, Lens) concurrently. The choice is between `asyncio` (cooperative multitasking) and `threading` (OS-level threads) for handling concurrent I/O.

### Decision

**Use `asyncio` exclusively.** All network I/O is async. No threading for I/O-bound operations. CPU-bound work (image processing) uses `asyncio.to_thread()`.

### Consequences

**Positive:**
- Single-threaded concurrency — no G contention, no race conditions
- Natural fit for `httpx.AsyncClient` — designed for asyncio
- Textual is async-native — widgets use `async def` event handlers
- Lower memory overhead than threads (thousands of coroutines vs. hundreds of threads)
- Backpressure naturally handled — `asyncio.gather` with semaphore
- Cleaner cancellation — `asyncio.CancelledError` vs. thread joins

**Negative:**
- Learning curve — developers must understand `async`/`await`
- Blocking code in async context crashes the event loop
- Debugging harder — stack traces span event loop callbacks
- Third-party libraries may not support asyncio
- Cannot use standard synchronous file I/O in async handlers

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Threading** | Familiar, works with sync libraries | GIL limits parallelism, race conditions, higher memory | Rejected — inferior for I/O-bound work |
| **Multiprocessing** | True parallelism, bypasses GIL | Process overhead, no shared memory, complex IPC | Rejected — overkill for HTTP I/O |
| **Sync + concurrent.futures** | Simple, works everywhere | Thread pool overhead, no natural backpressure | Rejected — asyncio is superior for this use case |
| **Trio** | Structured concurrency, better than asyncio | Smaller ecosystem, not stdlib | Rejected — asyncio is stdlib and sufficient |
| **AnyIO** | Abstraction over asyncio/trio | Additional dependency | Rejected — unnecessary abstraction |

---

## ADR-007: JSON Columns Over Normalized Schema

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #database #schema #json

### Context

Patent API responses are deeply nested, semi-structured, and change without warning. A USPTO response has different fields than a WIPO response. Normalizing this into rigid SQL tables would require constant schema migrations.

### Decision

**Store patent data as JSON in SQLite TEXT columns.** Use SQLite's JSON1 extension for queries. Denormalize only fields needed for `ORDER BY` (e.g., `citation_count`).

### Consequences

**Positive:**
- Schema flexibility — new API fields automatically supported
- No migrations when APIs add/remove fields
- Fast reads — single `SELECT` returns full patent record
- Natural fit for Python `dataclasses` — `json.dumps()` / `json.loads()`
- SQLite JSON1 functions for querying nested data

**Negative:**
- No type enforcement at database level — bad data only caught in Python
- Cannot create foreign keys to nested JSON fields
- `ORDER BY` on JSON fields requires `json_extract()` — slower than indexed columns
- Storage slightly larger than normalized (repeated keys)
- Querying across JSON arrays (e.g., all inventors) is verbose

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Fully normalized schema** | Type safety, referential integrity, efficient queries | Fragile to API changes, constant migrations | Rejected — APIs change too frequently |
| **Hybrid (normalized core + JSON metadata)** | Best of both worlds | Complex, still needs migrations for core fields | Rejected — over-engineered for MVP |
| **JSON columns with denormalized indexes** | Flexible + fast queries | Slightly more storage, manual sync | **Chosen** — optimal balance |
| **Document store (MongoDB)** | Native JSON, flexible | Requires separate database, not stdlib | Rejected — SQLite is sufficient |

---

## ADR-008: httpx Over requests

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #http #client #async

### Context

Python has two dominant HTTP client libraries: `requests` (synchronous, most popular) and `httpx` (sync + async, modern). RECON needs async HTTP for concurrent API calls.

### Decision

**Use `httpx` as the exclusive HTTP client.** No `requests`, no `urllib3` directly, no `aiohttp`.

### Consequences

**Positive:**
- Native async support — `httpx.AsyncClient` is first-class
- API-compatible with `requests` — easy to learn for requests users
- HTTP/2 support — multiplexed connections to APIs
- Built-in connection pooling — `AsyncClient` reused across requests
- Timeout configuration per-request
- Streaming responses supported
- Type hints throughout

**Negative:**
- Slightly larger than `requests` (but `requests` pulls in `urllib3` anyway)
- Newer — some edge cases less documented than `requests`
- `httpx` 0.x had breaking changes; now stable at 1.x

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **requests** | Most popular, best docs | Sync only, requires `requests-futures` or threads for async | Rejected — async is core requirement |
| **aiohttp** | Fast, mature async | Different API from requests, heavier, more complex | Rejected — httpx API is cleaner |
| **urllib3 (stdlib)** | No dependency | Low-level, verbose, no async | Rejected — too much boilerplate |
| **httpx** | Modern, async-native, requests-compatible | Slightly newer ecosystem | **Chosen** — best fit for architecture |

---

## ADR-009: Single-Process Over Client-Server

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #deployment #architecture #process-model

### Context

Modern applications often split into client-server architectures: a backend API (FastAPI/Flask) and a frontend (React/Vue). Even desktop apps sometimes run a local server. This enables web access, multi-user support, and separation of concerns.

### Decision

**RECON runs as a single Python process.** No background daemon, no local server, no HTTP listener. The CLI and TUI are the same process. When the user quits, everything stops.

### Consequences

**Positive:**
- Zero background processes — no `ps aux | grep recon` cleanup
- No port conflicts — nothing listening on localhost
- Simple mental model — one command, one process
- Easy debugging — `pdb` stops the entire application
- No serialization overhead — Python objects passed directly, no JSON over HTTP
- No CORS, no authentication between client/server
- Works in restricted environments (corporate laptops that block local servers)

**Negative:**
- Cannot access TUI from remote machine (must SSH and run locally)
- No multi-user support (acceptable: single-user tool)
- No web API for integration with other tools
- TUI and CLI share the same event loop — blocking one blocks both
- Must reload to pick up code changes

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Client-server (FastAPI + TUI client)** | Web access, multi-user, API for integrations | Requires server process, serialization overhead, complexity | Rejected — violates terminal-native principle |
| **Local daemon + CLI client** | Daemon stays warm, faster subsequent queries | Background process, port management, IPC complexity | Rejected — overkill for research tool |
| **Single process** | Simple, zero infrastructure, no background noise | No remote access, no multi-user | **Chosen** — aligns with minimalism |

---

## ADR-010: rapidfuzz Over ML Semantic Search

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #scoring #matching #ai #deterministic

### Context

Cross-reference intelligence requires matching patent entities (assignees, inventors, titles) across disparate data sources (USPTO, NIH, SEC, OpenAlex). ML approaches (embeddings, semantic similarity) offer better accuracy but introduce non-determinism and dependencies.

### Decision

**Use `rapidfuzz` (Levenshtein distance) for all entity matching.** Three-tier strategy: exact match (100) > fuzzy match (80-99) > co-occurrence (60-79). Equal-weight scoring: +20 per signal, max 100.

### Consequences

**Positive:**
- Deterministic — same input always produces same score
- Fast — C++ backend, millions of comparisons per second
- No model downloads — single pip install
- Transparent — user can understand why score is 80
- No GPU required — runs on any CPU
- Offline — no API calls for matching

**Negative:**
- Cannot match "Apple Inc." to "Apple Computer" if strings differ significantly
- No semantic understanding — "battery" and "cell" are distant
- Requires manual tuning of thresholds
- No learning from user feedback

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Sentence Transformers (embeddings)** | Semantic matching, understands synonyms | Model download (~500MB), GPU recommended, non-deterministic | Rejected — violates zero-AI default |
| **OpenAI embeddings API** | Best accuracy, no local model | API cost, network dependency, non-deterministic | Rejected — violates zero-AI and offline principles |
| **TF-IDF + cosine similarity** | Lightweight, explainable | Still requires corpus training, less accurate than embeddings | Rejected — rapidfuzz is simpler and sufficient |
| **rapidfuzz (fuzzy string)** | Fast, deterministic, offline, transparent | No semantic understanding | **Chosen** — optimal for MVP |

---

## ADR-011: 24% Rate Limit Headroom

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #resilience #rate-limiting #apis

### Context

Patent APIs have rate limits: USPTO ~100/min, EPO ~4/sec, WIPO ~100/day. Exceeding limits results in 429 errors, IP bans, or account suspension. The question is what safety margin to maintain.

### Decision

**Use 24% headroom:** cap at 76% of the published rate limit. USPTO: 76/min (not 100). EPO: 3/sec (not 4). WIPO: 76/day (not 100). Backoff strategy: 1s → 2s → 4s → 8s on 429 errors.

### Consequences

**Positive:**
- Never hits hard rate limit under normal operation
- Accommodates clock skew and API-side counting discrepancies
- Burst tolerance — short spikes don't trigger bans
- Graceful degradation — backoff instead of hard failure
- Respects API providers — good citizenship reduces ban risk

**Negative:**
- 24% slower maximum throughput than theoretical limit
- Other applications sharing the API key may still exceed limit
- Some APIs have unpublished limits — 24% may not be enough
- Backoff adds latency to user experience

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **100% utilization** | Maximum throughput | Risk of 429s, account bans | Rejected — too aggressive |
| **50% headroom** | Very safe | Too slow, wastes quota | Rejected — overly conservative |
| **10% headroom** | Near-maximum speed | Insufficient for clock skew | Rejected — too risky |
| **24% headroom** | Balanced safety and speed | Slightly slower | **Chosen** — empirical sweet spot |
| **Dynamic (token bucket)** | Adaptive to API behavior | Complex, may still exceed | Rejected — simple fixed limit is sufficient |

---

## ADR-012: Dry Error Voice Over Stacktraces

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #ux #error-handling #voice

### Context

When patent APIs fail, users see errors. The default Python behavior is a full stack trace — intimidating, unhelpful, and revealing internal paths. Most tools show generic "Something went wrong" messages — equally unhelpful.

### Decision

**Dry, actionable error voice.** Every error message: starts with `ERR:`, explains what happened in one line, suggests a fix, never shows stack traces in standard output. Log files contain full traces for debugging.

### Consequences

**Positive:**
- Users know exactly what failed and why
- No intimidation from Python stack traces
- Actionable — user can fix the issue (set API key, check network)
- Professional — feels like a polished tool, not a prototype
- Secure — no internal paths or architecture leaked in errors

**Negative:**
- Requires discipline — every `except` block must craft a message
- More code than `except Exception as e: print(e)`
- Developers debugging need to check log files
- Cannot use generic error handlers — must be context-specific

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Full stack traces** | Complete debugging info | Intimidating, leaks internals, unactionable | Rejected — poor UX |
| **Generic messages** | Simple to implement | Unhelpful, frustrating | Rejected — violates transparency |
| **Dry actionable voice** | Professional, helpful, secure | Requires effort per error site | **Chosen** — aligns with constitution |

---

## ADR-013: Inline Static Over Modal Dialogs

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #tui #ux #modals

### Context

Textual supports `ModalScreen` for overlay dialogs. Most TUI applications use modals for help, confirmations, and settings. However, modals interrupt workflow, require explicit dismissal, and feel like "popups."

### Decision

**No modal dialogs.** All overlays are inline `Static` widgets that appear within the current screen layout. Help overlay is a floating `Static` panel toggled with `?`. No `ModalScreen` anywhere in the codebase.

### Consequences

**Positive:**
- Non-blocking — user can continue working while help is visible
- Keyboard flow uninterrupted — no "press Escape to continue"
- Consistent with terminal philosophy — everything is inline
- Simpler code — no push_screen/pop_screen state management
- Faster — no screen transition animation

**Negative:**
- Help overlay may obscure content (mitigated: toggle with `?`)
- No dimmed background to indicate "modal" state
- Less familiar to users accustomed to GUI modal dialogs
- Cannot stack multiple overlays easily

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **ModalScreen for everything** | Familiar, clear focus, standard pattern | Blocking, interrupts flow, more complex state | Rejected — violates keyboard-first philosophy |
| **Inline Static with dimming** | Non-blocking, visual focus indicator | Requires CSS for dimming | **Chosen** — optimal balance |
| **Notification toasts only** | Minimal interruption | Insufficient for complex help content | Rejected — help needs space |

---

## ADR-014: Phase-Based Git Commits

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #git #workflow #history

### Context

Git history can be a mess: random commits, "fix typo", "wip", "asdf". For a project with distinct development phases (Foundation → Core Search → Preview → Intelligence → Collections → Polish), the history should tell the story of the project's evolution.

### Decision

**Commit by phase.** Each major development phase is one logical commit (or a small series). Commit messages follow Conventional Commits with phase context: `feat: Phase 2 — Core Patent Search & Navigation`.

### Consequences

**Positive:**
- History tells a story — `git log` reads like a changelog
- Easy bisection — find which phase introduced a bug
- Clean diffs — each commit is a coherent feature set
- Professional — shows intentional development, not hacking
- Easy to review — one commit per phase

**Negative:**
- Retroactive commits require `git add -p` or rebase
- Large commits are harder to review in detail
- Cannot easily cherry-pick a single file from a phase
- Requires discipline — no "quick fix" commits

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Commit-per-file** | Granular, easy cherry-pick | Noisy history, loses phase context | Rejected — too granular |
| **Commit-per-day** | Simple habit | Meaningless messages, mixed features | Rejected — poor history |
| **Commit-per-feature (within phase)** | Balance of granularity and context | Requires careful feature definition | Considered — acceptable for future |
| **Phase-based commits** | Storytelling history, clean milestones | Large commits, retroactive effort | **Chosen** — optimal for this project |

---

## ADR-015: Kitty > iTerm2 > Sixel > Fallback Image Chain

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #images #terminal-protocols #rendering

### Context

Patent documents contain diagrams, figures, and drawings. Displaying these in a terminal requires terminal-specific image protocols. There is no universal standard — each terminal emulator implements its own.

### Decision

**Priority chain:** Kitty graphics protocol > iTerm2 inline images > Sixel > external viewer fallback (`xdg-open`). Detect terminal capability at runtime via environment variables (`KITTY_WINDOW_ID`, `TERM_PROGRAM`, `TERM`).

### Consequences

**Positive:**
- Best possible image quality on supported terminals (Kitty/iTerm2)
- Graceful degradation — always some way to view images
- No dependencies beyond Pillow (already required)
- External viewer fallback works on any terminal
- User can choose terminal based on image needs

**Negative:**
- Three code paths to maintain for image rendering
- Sixel support is limited and buggy in many terminals
- External viewer breaks the "terminal-native" flow
- Cannot display images in basic terminals (xterm, GNOME Terminal) without fallback
- Image caching complex — must store rendered escape sequences

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Kitty only** | Best quality, simplest code | Excludes iTerm2 users, no fallback | Rejected — too restrictive |
| **Sixel only** | Standard-ish, works in many terminals | Limited support, buggy, low quality | Rejected — insufficient coverage |
| **ASCII art only** | Universal, no dependencies | Unreadable for complex diagrams | Rejected — defeats purpose |
| **External viewer only** | Universal, full quality | Breaks terminal flow, requires GUI | Rejected — not terminal-native |
| **Priority chain** | Best quality where possible, fallback everywhere | Multiple code paths | **Chosen** — optimal coverage |

---

## ADR-016: stdlib json Over orjson

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #serialization #performance #dependencies

### Context

JSON serialization/deserialization is a hot path for cache operations. `orjson` is a Rust-based JSON library that claims 28x speedup over stdlib `json`. However, it adds a native dependency.

### Decision

**Use stdlib `json` exclusively.** No `orjson`, no `ujson`, no `simdjson`. Cache responses are <100KB — stdlib performance is sufficient.

### Consequences

**Positive:**
- Zero additional dependencies
- No platform-specific wheels (orjson requires Rust compiler on some platforms)
- No security surface from C/Rust extensions
- Works on every Python installation
- Patent API responses are small — performance difference is negligible

**Negative:**
- ~28x slower than orjson for large payloads (irrelevant for <100KB)
- No native datetime serialization (handled in Python)
- No JSON schema validation (handled manually)

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **orjson** | 28x faster, handles datetimes | Native dependency, Rust toolchain for source builds | Rejected — violates minimal dependency constitution |
| **ujson** | Faster than stdlib, pure Python fallback | Still an extra dependency, less maintained | Rejected — unnecessary |
| **stdlib json** | Zero deps, universal, sufficient | Slower for large payloads | **Chosen** — performance acceptable for use case |

---

## ADR-017: No Certificate Pinning

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #security #tls #trust

### Context

Certificate pinning hardcodes expected TLS certificates for API endpoints, preventing MITM attacks even if a CA is compromised. However, it breaks when certificates rotate.

### Decision

**No certificate pinning.** Rely on standard CA validation via `certifi`/`ssl` module. Trust the system's certificate store.

### Consequences

**Positive:**
- No breakage when API providers rotate certificates
- No maintenance burden to update pinned certs
- Standard TLS validation is sufficient for public patent APIs
- Works behind corporate proxies that do SSL inspection

**Negative:**
- Vulnerable to compromised CA (extremely rare for major CAs)
- No protection against rogue DNS at the local network level
- Less paranoid than some security models require

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Pin all API certificates** | Maximum security | Breaks on cert rotation, maintenance burden | Rejected — overkill for public data |
| **Pin root CA only** | Balanced | Still requires updates if CA changes | Rejected — minimal gain |
| **Standard CA validation** | Zero maintenance, standard security | Theoretical CA compromise risk | **Chosen** — sufficient for patent research |

---

## ADR-018: No RBAC/ABAC/ACL

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #authorization #security #single-user

### Context

Most applications implement role-based access control (RBAC), attribute-based access control (ABAC), or access control lists (ACL). These systems manage who can do what within the application.

### Decision

**No RBAC, ABAC, or ACL.** RECON is a single-user application. The OS user is the only actor. Unix file permissions (0600 for config, 0700 for data directory) are the sole access control mechanism.

### Consequences

**Positive:**
- Zero code complexity for authorization
- No user management, roles, or permissions tables
- No authentication flow within the application
- OS-level security is robust and well-understood
- No "admin" backdoors or privilege escalation risks

**Negative:**
- Cannot share a single installation between users (must install per-user)
- No audit trail of "who did what" (acceptable: single user)
- Cannot restrict features within the app (all features available to the user)

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **RBAC (admin/user/guest)** | Fine-grained control | Massive overkill for single-user tool | Rejected — unnecessary complexity |
| **ABAC (attribute-based)** | Flexible, dynamic | Even more complex than RBAC | Rejected — absurd for this use case |
| **OS permissions only** | Simple, robust, zero code | No in-app restrictions | **Chosen** — optimal for single-user tool |

---

## ADR-019: File-Based Secrets Over Environment Variables

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #security #secrets #configuration

### Context

API keys (USPTO, EPO, Lens) must be stored securely. Common approaches: environment variables, `.env` files, keyrings, cloud secret managers, or config files.

### Decision

**Store secrets in `~/.config/recon/config.toml` with 0600 permissions.** No environment variables for secrets. No `.env` files. Keys loaded at startup and held in memory.

### Consequences

**Positive:**
- Not visible in `/proc/*/environ` (unlike env vars)
- Not leaked via shell history (unlike command-line flags)
- Explicit file permissions — `chmod 0600` enforced on write
- Portable across shells — no `.bashrc` pollution
- Version-controllable format (TOML)
- Easy backup/restore — single file

**Negative:**
- File must be manually secured on shared systems
- No automatic rotation
- Plaintext in memory (unavoidable — must use keys to call APIs)
- Backup tools may sync the file to cloud (user responsibility)

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Environment variables** | Standard 12-factor app pattern | Visible in `/proc`, shell history, process lists | Rejected — insecure for local tool |
| **`.env` files** | Simple, popular | Same visibility issues, easy to accidentally commit | Rejected — same problems |
| **OS keyring (keyring lib)** | Encrypted storage | Extra dependency, platform differences | Rejected — adds dependency, marginal gain |
| **Cloud secret managers** | Enterprise-grade | Requires network, vendor lock-in, overkill | Rejected — offline tool |
| **Config file (0600)** | Controllable, portable, explicit | User must secure file | **Chosen** — best balance for single-user tool |

---

## ADR-020: No Horizontal Scaling

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #scalability #architecture #scope

### Context

Applications are often designed with horizontal scaling in mind: multiple instances behind a load balancer, distributed databases, message queues. This enables handling millions of users.

### Decision

**RECON will never horizontally scale.** It is a single-user, single-process tool. If performance becomes an issue, the answer is "buy a faster laptop," not "add more servers."

### Consequences

**Positive:**
- No distributed systems complexity
- No consistency models, CAP theorem, or consensus protocols
- No message queues, load balancers, or service discovery
- SQLite is sufficient — no need for PostgreSQL cluster
- Simple mental model — one process, one database file

**Negative:**
- Cannot serve multiple users simultaneously (by design)
- Cannot offload heavy computation to a server farm
- Cache is local to one machine (not shared across devices)
- Maximum throughput limited by single-machine resources

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Microservices** | Scalable, independent deploys | Massive complexity, network latency, debugging hell | Rejected — absurd for CLI tool |
| **Serverless (Lambda/Cloud Functions)** | Auto-scale, pay-per-use | Cold starts, vendor lock-in, no terminal access | Rejected — incompatible with terminal-native |
| **Single-process vertical scaling** | Simple, fast, zero infra | Limited to one machine | **Chosen** — optimal for use case |

---

## ADR-021: Typer Over argparse

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #cli #framework #typing

### Context

Python's standard library includes `argparse` for CLI argument parsing. `click` is the most popular third-party alternative. `typer` is a newer library built on `click` with native type hint support.

### Decision

**Use `typer` for CLI construction.** No `argparse`, no raw `click`. Type hints drive CLI generation.

### Consequences

**Positive:**
- Type hints become CLI arguments — `query: str` → `--query TEXT`
- Automatic `--help` generation from docstrings
- Native async support via `async def` commands
- Nested subcommands: `recon config set --uspto-key XXX`
- Shell completion generation
- Validation from type hints — `limit: int = 10` validates automatically

**Negative:**
- Extra dependency (but small — builds on `click`)
- Less control than raw `argparse` for exotic CLI patterns
- `click` dependency pulled in transitively

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **argparse (stdlib)** | Zero dependencies, always available | Verbose, no type hints, manual help text | Rejected — too much boilerplate |
| **click** | Mature, battle-tested | No native type hint support | Rejected — typer supersedes it |
| **typer** | Type-native, modern, clean | Extra dependency | **Chosen** — best developer experience |

---

## ADR-022: fpdf2 Over reportlab

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #pdf #export #dependencies

### Context

PDF export is required for patent collections. Python has two major PDF libraries: `reportlab` (mature, commercial heritage) and `fpdf2` (modern, simpler API).

### Decision

**Use `fpdf2` for PDF generation.** No `reportlab`. Simple API for tables, text, and basic formatting.

### Consequences

**Positive:**
- Simple API — `pdf.cell()`, `pdf.multi_cell()`, `pdf.output()`
- UTF-8 support out of the box
- Smaller than reportlab
- Active maintenance (fpdf2 is a fork of abandoned fpdf)
- Sufficient for patent data tables and text

**Negative:**
- Less powerful than reportlab for complex layouts
- No built-in HTML-to-PDF conversion
- Limited charting/diagram support
- Table formatting requires manual cell positioning

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **reportlab** | Very powerful, mature | Complex API, larger, commercial license history | Rejected — overkill for simple tables |
| **WeasyPrint** | HTML-to-PDF, beautiful | Requires GTK dependencies, heavy | Rejected — too heavy for CLI tool |
| **pdfkit (wkhtmltopdf)** | Webkit rendering | Requires external binary | Rejected — external dependency |
| **fpdf2** | Simple, UTF-8, maintained | Less powerful | **Chosen** — sufficient for patent exports |

---

## ADR-023: No Soft Deletes

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #data-lifecycle #database #scope

### Context

Soft deletes (marking records as deleted instead of removing them) are common in multi-user applications for audit trails and recovery. They add complexity: `deleted_at` columns, filtered queries, periodic cleanup jobs.

### Decision

**Hard deletes only.** No `deleted_at` columns. No `is_active` flags. When a user deletes a collection or clears cache, the data is permanently removed.

### Consequences

**Positive:**
- Simple queries — no `WHERE deleted_at IS NULL` on every SELECT
- Smaller database — deleted data reclaims space immediately
- No cleanup jobs — no background process to purge old soft-deleted records
- Clear mental model — delete means delete
- SQLite `VACUUM` reclaims space efficiently

**Negative:**
- No recovery from accidental deletion
- No audit trail of what was deleted when
- Cannot implement "undo" feature later
- Violates some compliance requirements (not applicable: personal tool)

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Soft deletes everywhere** | Recoverable, auditable | Complex queries, storage bloat, cleanup jobs | Rejected — overkill for personal tool |
| **Soft deletes for collections only** | Partial safety | Inconsistent, still complex | Rejected — partial solutions are worse |
| **Hard deletes only** | Simple, clean, fast | No recovery | **Chosen** — acceptable for single-user cache |

---

## ADR-024: SHA256 Query Hash Over Auto-Increment PK

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #caching #database #performance

### Context

Cache entries need a primary key. Options: auto-incrementing integers (standard), UUIDs (universal), or content-based hashes (deterministic).

### Decision

**Use SHA256(query_string + source_list + limit) as the cache primary key.** Deterministic, collision-resistant, cache hits are exact string matches.

### Consequences

**Positive:**
- Deterministic — same query always produces same key
- No sequence management — no `AUTOINCREMENT`, no gaps
- Natural deduplication — identical queries overwrite same row
- Portable — key is derived from content, not database state
- Distributed-safe — no coordination needed for key generation

**Negative:**
- 64-character hex strings — slightly larger than integers
- Hash computation overhead — negligible for SHA256 on short strings
- Cannot determine insertion order from key alone — use `cached_at` timestamp
- Query normalization required — `"battery"` and `"battery "` hash differently

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Auto-increment integer** | Small, fast, ordered | Requires sequence, not portable, no natural dedup | Rejected — doesn't solve cache dedup |
| **UUID v4** | Universal, no collision | Random, no dedup, larger than integers | Rejected — no benefit for this use case |
| **SHA256 content hash** | Deterministic, dedup, portable | Larger keys, hash overhead | **Chosen** — optimal for cache semantics |

---

## ADR-025: Concurrent API Gather Over Sequential

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #performance #concurrency #apis

### Context

A patent search queries multiple APIs (USPTO, WIPO, EPO, Google, Lens). These calls are independent — no API's results depend on another's. The question is whether to call them sequentially or concurrently.

### Decision

**Use `asyncio.gather()` for concurrent API calls.** All sources queried in parallel. Results merged and sorted after all responses return (or timeout).

### Consequences

**Positive:**
- Search latency = slowest API, not sum of all APIs
- ~3-5x faster than sequential for 5 sources
- Natural fit with `httpx.AsyncClient`
- Timeout per-source — slow API doesn't block others
- Results richer — more sources = more patents

**Negative:**
- Higher instantaneous resource usage — 5 concurrent connections
- Harder to debug — which API failed in the gather?
- Rate limits apply per-source simultaneously — must respect all
- Results arrive out of order — must sort after gather
- One slow API delays the entire result set (mitigated: per-source timeout)

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Sequential calls** | Simple, easy to debug, lower resource use | Slow — sum of all API latencies | Rejected — too slow for interactive use |
| **Concurrent gather** | Fast, efficient | Complex error handling, resource spikes | **Chosen** — speed is critical |
| **Prioritized sequential** | Fastest API first, then others | Complex, first API may be incomplete | Rejected — over-engineered |

---

## ADR-026: Lazy Loading Over Eager Fetching

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #performance #tui #loading

### Context

Patent preview tabs show: Info (always needed), Claims (text-heavy), Image (binary-heavy). Fetching all three on every search result would be wasteful — most patents are never previewed.

### Decision

**Lazy load Claims and Image tabs.** Only fetch when user activates the tab. Info tab loads immediately with search results. Image tab shows placeholder until activated.

### Consequences

**Positive:**
- Faster initial search results — no claims/images fetched upfront
- Less bandwidth — only fetch what's viewed
- Less API quota consumed — image APIs often have stricter limits
- Faster TUI navigation — results list populates in <100ms
- Better perceived performance

**Negative:**
- Tab switching has loading delay — "fetching claims..." indicator needed
- Image tab may be slow on first view — requires network round-trip
- Cannot pre-cache claims for offline reading
- More complex state management — track which tabs are loaded

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Eager fetch all** | Instant tab switching | Slow search, wasted bandwidth, quota exhaustion | Rejected — poor resource utilization |
| **Lazy load claims, eager images** | Balance | Images are largest payload | Rejected — inconsistent |
| **Lazy load claims and images** | Fast search, efficient | Tab switch delay | **Chosen** — optimal for interactive use |

---

## ADR-027: No Docker, No Kubernetes

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #infrastructure #deployment #scope

### Context

Containerization (Docker) and orchestration (Kubernetes) are standard for modern application deployment. They provide isolation, reproducibility, and scaling.

### Decision

**No Docker. No Kubernetes. No containers.** RECON is installed via `pip install` or `pip install -e .` directly into a Python virtual environment.

### Consequences

**Positive:**
- Zero container overhead — no Docker daemon, no image layers
- Native performance — no virtualization penalty
- Simple installation — `pip install recon` or clone + `pip install -e .`
- Works on any system with Python 3.12+ — no Docker compatibility issues
- Development is instant — no `docker build`, no image pushes
- Debugging is native — `pdb`, `print()`, IDE integration

**Negative:**
- No reproducible environment — Python version and system libraries vary
- No isolation from system Python packages
- Cannot deploy to container-only platforms (some corporate environments)
- User must manage their own Python environment

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Docker container** | Reproducible, isolated | Overhead, complexity, not terminal-native | Rejected — overkill for CLI tool |
| **Docker + docker-compose** | Multi-service if needed | Even more overhead | Rejected — single process, no services |
| **Kubernetes** | Enterprise scaling | Absurd complexity for CLI tool | Rejected — completely inappropriate |
| **pip + venv** | Simple, native, fast | Environment variance | **Chosen** — optimal for Python CLI |

---

## ADR-028: 100-Character Line Length

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #code-style #formatting #readability

### Context

Line length limits affect code readability and diff review. PEP 8 recommends 79 characters (historical terminal width). Modern displays support much more. Black defaults to 88. Some teams use 120.

### Decision

**100-character line length.** Formatted with `black --line-length 100`. `isort` and `flake8` configured to match.

### Consequences

**Positive:**
- Fits side-by-side diffs on 1920x1080 displays
- More expressive per line than 79 — less vertical scrolling
- Still readable on laptops — not so long that wrapping occurs
- Accommodates Textual widget class hierarchies without excessive breaking
- Modern standard — many projects have moved beyond 80

**Negative:**
- Slightly longer than PEP 8 recommendation
- Some older tools assume 80 columns
- Very deeply nested Textual callbacks may still exceed 100

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **79 (PEP 8)** | Standard, historical | Too short for modern code, excessive line breaks | Rejected — outdated for this project |
| **88 (Black default)** | Popular, reasonable | Still tight for long widget names | Rejected — slightly too short |
| **100** | Modern, readable, practical | Non-standard length | **Chosen** — optimal for this codebase |
| **120** | Very spacious | Side-by-side diffs may not fit on smaller screens | Rejected — too long |

---

## ADR-029: No Alembic, Versioned SQL Migrations

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #database #migrations #schema

### Context

Database schema evolution requires migration tools. Alembic (SQLAlchemy's migration tool) is the Python standard. It tracks schema versions, generates migration scripts, and handles upgrades/downgrades.

### Decision

**No Alembic.** Schema migrations are versioned SQL files in `migrations/v{N}/schema.sql`. A simple Python runner executes them in order. SQLite's flexible schema (JSON columns) minimizes the need for migrations.

### Consequences

**Positive:**
- Zero additional dependencies — Alembic requires SQLAlchemy
- Simple — SQL files are transparent and auditable
- Sufficient for SQLite — schema changes are rare (JSON flexibility)
- No migration generation complexity — write SQL by hand
- Easy to understand — any developer can read a `.sql` file

**Negative:**
- No automatic migration generation from model changes
- No downgrade safety — must write reverse migrations manually
- No migration history table — tracked via filename convention
- Cannot use Alembic's branching/merge features

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **Alembic + SQLAlchemy** | Standard, automatic generation, robust | Adds SQLAlchemy dependency, complex for simple schema | Rejected — overkill for SQLite |
| **Django migrations** | Integrated with ORM | Requires Django, completely wrong ecosystem | Rejected — inappropriate |
| **Raw SQL files + runner** | Simple, transparent, zero deps | Manual, no automation | **Chosen** — sufficient for this project |

---

## ADR-030: EPO OAuth2 Over API Key

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** Project Lead
- **Tags:** #authentication #oauth #epo #apis

### Context

The European Patent Office (EPO) Open Patent Services (OPS) API uses OAuth 2.0 client credentials flow for authentication. This requires a consumer key and secret to obtain a bearer token, unlike USPTO's simple API key.

### Decision

**Implement full OAuth 2.0 client credentials flow for EPO.** Store `epo_consumer_key` and `epo_consumer_secret` in config. Handle token acquisition, caching, and automatic refresh. No API key alternative for EPO.

### Consequences

**Positive:**
- Official EPO authentication — guaranteed compatibility
- Token caching — avoid re-authenticating every request
- Automatic refresh — seamless user experience
- Standard OAuth 2.0 — well-documented, libraries available

**Negative:**
- More complex than API key — token endpoint, expiration handling
- Requires token storage — in-memory only (security)
- Two secrets instead of one — consumer key + consumer secret
- Token expiration edge cases — clock skew, network failures during refresh
- OAuth library dependency — `httpx` can handle it manually, but verbose

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **OAuth 2.0 full implementation** | Official, robust | Complex | **Chosen** — required by EPO |
| **OAuth2 client library (authlib)** | Simpler code | Extra dependency | Rejected — httpx can handle OAuth2 client credentials |
| **Skip EPO** | Simpler codebase | Lose major patent jurisdiction | Rejected — EPO is critical |
| **Scrape Espacenet** | No auth | Fragile, illegal, unreliable | Rejected — violates terms of service |

---

## Appendix A: ADR Template

Use this template for future ADRs:

```markdown
## ADR-XXX: [Title]

- **Status:** Proposed / Accepted / Deprecated / Superseded
- **Date:** YYYY-MM-DD
- **Deciders:** [names]
- **Tags:** #tag1 #tag2

### Context

[What is the issue that we're seeing that is motivating this decision or change?]

### Decision

[What is the change that we're proposing or have agreed to implement?]

### Consequences

**Positive:**
- [Consequence 1]
- [Consequence 2]

**Negative:**
- [Consequence 1]
- [Consequence 2]

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|:---|:---|:---|:---|
| **[Option A]** | [Pros] | [Cons] | [Chosen/Rejected] |
| **[Option B]** | [Pros] | [Cons] | [Chosen/Rejected] |

### Notes

[Any additional context, links, or references]
```

---

## Appendix B: How to Propose a New ADR

1. **Copy the template** from Appendix A
2. **Assign the next ADR number** (check the index above)
3. **Set status to `Proposed`**
4. **Open a discussion** in the project (or with the team)
5. **After consensus, change status to `Accepted`**
6. **Update the ADR Index** table at the top of this document
7. **Commit** with message: `docs(adr): ADR-XXX — [Title]`

---

## Appendix C: Superseding an ADR

If a decision changes:

1. **Update the old ADR:** Change status to `Superseded by ADR-YYY`
2. **Create new ADR:** Use the template, reference the old ADR
3. **Update the index:** Mark old as Superseded, add new
4. **Document migration path:** How to move from old to new decision

---

*End of Architecture Decision Records*
