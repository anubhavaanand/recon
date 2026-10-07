# RECON — Design History & Original Vision

Recovered from the original design transcripts (May–Sep 2026, "RECON Phase 2 Overview",
"RECON SEARCH 1", "Recon 3", "RECON GUIDE docs", "Read Request"). This document preserves
the interface vision, the constitution, and every accepted design decision so the project
no longer depends on Word documents in a Downloads folder.

---

## 1. Original Concept (Phase 2, May 2026)

RECON was conceived as a terminal-native patent research tool with a **zero-cost stack**
(free APIs only, no subscriptions), inline terminal graphics, and a **k9s + ncspot hybrid**
UI aesthetic — minimal chrome, keyboard-first, information-dense.

The original interface sketch (single rectangular panel):

```
┌─ RECON: Search ─────────────────────────────┐
│ Query: [semiconductor packaging substrate] │
│ Sources: [●Google] [●USPTO] [○EPO] [○WIPO] │
│ Mode: [Boolean ▼] AI: [OFF]                │
├─────────────────────────────────────────────┤
│ #  Title                          Date Src  │
│ 1  Flip-chip bonding method...   2024 G   │
│ 2  Substrate for semiconductor    2023 U   │
│ 3  Packaging structure with...     2025 G   │
│                                             │
│ [↑↓]Navigate [Enter]Preview [a]Add [q]Quit │
└─────────────────────────────────────────────┘
```

**Superseded by design evolution, not abandonment.** The single-panel sketch grew into the
three-pane layout defined in `.specify/docs/frontend.md` §7 (search on top, ResultList left
~40%, Info/Claims/Image tabs right ~60% at ≥120 cols; compact and minimal tiers below that).
The sketch's *elements* all survived:

| Mockup element | Where it lives today |
|---|---|
| Query input | Search input (`/` focuses) |
| `Sources: [●Google] [●USPTO] ...` toggles | `S` source-filter overlay (per-search `--source` flag on CLI) |
| `Mode: [Boolean ▼]` | **Not implemented** — closest is the `x` semantic-search toggle |
| `AI: [OFF]` | Zero-AI constitution; `m` synthesis toggle (Ollama, opt-in) |
| Results table `# Title Date Src` | ResultList widget with year·age chips |
| Shortcut bar | Textual Footer |

## 2. The Constitution (10 non-negotiables)

1. **Zero-AI default** — no LLM/ML in the default path; optional AI is explicit opt-in.
2. **Transparency over persuasion** — every score shows its math (equal-weight, +20/signal, max 100).
3. **Terminal-native only** — no GUI, no web fallback, no Electron.
4. **Keyboard-first** — every feature has a shortcut; mouse is optional.
5. **No modal dialogs** — all overlays are inline widgets (help, export, source filter).
6. **Speed over depth** — <3s cached search, <100ms navigation; fast first response.
7. **Dry error voice** — `ERR: {reason}. {fix}` — actionable, no stacktraces, no apologies, no `!`.
8. **Minimal dependencies** — stdlib first; only add when absolutely necessary.
9. **Deterministic** — same query → same results (cache TTL permitting).
10. **Signal over noise** — unverified sources flagged `[?]` / `UNKNOWN`, never silently dropped.
    Descending sort that never removes entries.

## 3. Accepted Architecture Decision Records

| ADR | Decision | Rationale |
|---|---|---|
| ADR-001 | Textual as TUI framework | Async-native, CSS styling, built-in widgets; rejected Rich (too low-level), urwid (dated), curses (platform-specific) |
| ADR-002 | Zero-AI default | Patent research demands factual accuracy; hallucination risk unacceptable |
| ADR-003 | SQLite over PostgreSQL/Redis | Single-user tool; zero-config; single file backup |
| ADR-004 | Dataclasses, **Pydantic prohibited** | Zero dependency; `asdict()` serialization suffices |
| ADR-005 | Image priority: Kitty > iTerm2 > Sixel > external viewer | Best quality first, graceful degradation |
| ADR-006 | Dedup by patent family; merged results never dropped | Completeness over tidiness |
| ADR-007 | 24% rate-limit headroom (76/min on a 100/min API) + 1s→2s→4s→8s backoff | Never get throttled |
| ADR-008 | Cache: L1 session dict → L2 SQLite (30-day TTL, metadata; indefinite for documents; append-only citations) | Speed over depth |
| ADR-009 | Config at `~/.config/recon/config.toml`, chmod 600, **no env-var secrets** | `/proc/*/environ` leakage risk |
| ADR-010 | Phase-based conventional commits | Clean bisectable history |

**Prohibited stack** (per constitution): Pydantic, SQLAlchemy, orjson, uvloop, aiosqlite,
openai/anthropic SDKs, tkinter/PyQt, Docker/web fallbacks.

## 4. Data Sources — decision history

- **USPTO ODP** (`api.uspto.gov/api/v1`, X-API-KEY) — live. Keys via data.uspto.gov (ID.me verified).
- **WIPO PATENTSCOPE** — live, no key. Effectively limited (76/day).
- **EPO OPS** — OAuth 2.0; keys stored, client partial.
- **Google Patents** — original plan was mock-only ("scraping violates ToS" concern, 2026-05).
  **Reversed 2026-09**: switched to keyless scraping (DuckDuckGo + native Google Patents XHR
  endpoints) as the universal enrichment backbone. This was an explicit user decision
  ("im switching from api use to web scraping via duckduckgo search").
- **Lens.org** — API key; scraper-only path.
- **Indian patents (IP India)** — investigated and rejected: no official API, InPASS is
  CAPTCHA-gated; Indian coverage arrives via WIPO/Google/Lens instead.

## 5. Interface decisions (verbatim from the design chats)

- **Aesthetic**: k9s + ncspot hybrid — minimal chrome, spacing and subtle rules over heavy
  borders. Later refined with the "Hermes-quality" pass: clean status bar, keyboard hints in
  footer, **light/dark auto-detection** via `COLORFGBG`, instant first frame, spinner during
  async loads, overlay fades. Tokyo Night palette (`$bg #1a1b26`, `$primary #7aa2f7`,
  `$error #f7768e`, …) — see `.specify/docs/frontend.md` §11.
- **Three-tab preview** (Info / Claims / Image), claims + image **lazy-loaded on first tab
  activation only**, <100ms preview updates, <500ms lazy loads.
- **Reader mode** (`r`): no header/footer, full-width, `j/k` scroll, minimal status line.
- **Help overlay** (`?`): inline Static, never a ModalScreen.
- **Export overlay** (`e`): inline format selector (json/csv/bibtex/markdown/pdf).
- **Keyboard map** (PRD): `↑↓/j/k` navigate, `Enter` detail, `h/l` tabs, **1–9 quick-open**,
  `g/G` top/bottom, `s` save, `r` reader, `d` download, `e` export, `/` focus, `?` help,
  `q`/Esc back-quit. (All implemented; plus post-spec additions: `a` assignee portfolio,
  `w` sort & weights, `x` semantic toggle, `c` citations, `f` family tree, `t` translate,
  `n/p` figure navigation, `i` independent-claims filter, `S` source filter, `m` synthesis.)

## 6. Development history (the multi-agent workflow)

Built through a coordinator workflow: Kimi held the design knowledge and generated the
document set (PRD v1.0.0, Technical Architecture, Database Design, Security & Access
Control, README, CONTRIBUTING, Frontend Spec, ADR log, CHANGELOG); Gemini and Copilot
implemented against those documents; the human tested and committed per phase.

Phases: 1 Foundation → 2 Core Search → 3 Three-Tab Preview → 4 Cross-Reference
Intelligence → 5 Collections/Export/Reader → 6 Polish & Constitution Audit → v0.2.0 Live
APIs (USPTO+WIPO) → live-network hardening + keyless scraping pivot (2026-09) → TUI visual
redesign (Tokyo Night Pro, Sixel/Kitty rendering, headless frame-capture testing).

Historic bugs worth remembering (regression guardrails):
- Textual `ListView` has **no** `get_item_at()` — use `highlighted_child`.
- Textual prefixes tab IDs with `--content-tab-` — strip before matching.
- Rich markup eats `[x]` brackets — escape as `\[x]` or letters vanish.
- Lens.org IDs are longer than 12 chars — don't hard-slice patent IDs.
- Several USPTO legacy APIs (Office Action, Enriched Citation) were decommissioned to ODP
  on 2026-05-29 — don't reintroduce them; use `api.uspto.gov/api/v1`.

## 7. What the design docs still list as open

- Boolean query mode (`Mode: [Boolean ▼]` from the original sketch) — never built.
- EPO OAuth client completed end-to-end (token refresh wired into search aggregation).
- `expires` (expiration) date is still not populated by any client — shows `[?]`.
- `docs/` pipeline artifacts (RECON PRD v1.0.0 with 6 screen mockups, Security doc,
  full ADR log, DB design) were generated in chat but only partially committed — this file
  and `.specify/docs/*` are the surviving copies.

## 8. Source documents

- `~/Downloads/RECON Phase 2 Overview.docx` — original concept + rectangular mockup
- `~/Downloads/RECON SEARCH 1.docx` — phase history, v0.2.0 live APIs, USPTO key registration
- `~/Downloads/Recon 3.docx` — code review context, doc-generation sweep, full ADR + PRD text
- `~/Downloads/RECON GUIDE docs设计已掌.docx` — continuation point, security/README/CONTRIBUTING generation
- `~/Downloads/Read Request.docx` — status meta-summary and open-questions list
