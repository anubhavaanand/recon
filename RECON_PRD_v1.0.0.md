# RECON — Product Requirements Document
## Terminal-Native Patent Research Tool

**Version:** 1.0.0  
**Date:** 2026-05-13  
**Status:** Production Ready  
**Repository:** https://github.com/anubhavaanand/recon

---

## 1. Identity & Philosophy

RECON is a technology intelligence operative. It surfaces raw signals, correlates them deterministically, and lets the analyst draw conclusions. It treats the user as competent, not as a consumer.

### Core Principles (Constitution)

1. **Zero-AI Default** — Deterministic operation. No hidden LLM layers unless explicitly toggled.
2. **Transparency Over Persuasion** — Every score shows its math. Every signal links to source.
3. **Signal Over Noise** — Unverified sources marked `[unverified]`. Omission is a lie.
4. **Neutrality Over Hype** — EXPIRED→PUBLIC DOMAIN. ABANDONED→FREE TO USE.
5. **Equal Weights** — Each signal: +20. Max: 100. Penalties after sum.
6. **Descending Sort, Never Remove** — All entries visible. Ranked by confidence.
7. **Terminal-Native, No GUI Fallback** — Keyboard-first. Mouse discoverable, never required.
8. **Speed Over Depth** — Search <3s, Preview <1s, Deep dive on Enter only.
9. **Uncertainty Flagged** — Fuzzy match `○ 85%`, stale `[stale: date]`.
10. **Dry, Actionable Error Voice** — "USPTO timeout. Retrying in 4s."

---

## 2. Visual Design System

### Aesthetic: k9s + ncspot Hybrid

- **No boxes** — Horizontal rules (`─`) and spacing create structure
- **No heavy chrome** — Minimal borders, maximum information density
- **Keyboard-first** — All actions have hotkeys. Mouse is secondary.
- **Progressive disclosure** — Summary first, detail on demand, raw data always accessible

### Color & Typography

```
Score bar:     Unicode blocks ████░░ (instant visual assessment)
Signal dots:   ●●●●○ (quick source health)
Status pills:  ● ACTIVE  ● EXPIRED  ● ABANDONED
Tab indicator: [Info] [Claims] [Image] (active in brackets)
Error text:    ERR: prefix, no apologies, no fluff
```

### Layout Philosophy

```
Information Density > Decoration
Context-Sensitive Footer > Permanent Menu Bar
Inline Overlays > Modal Dialogs (prohibited)
Full-Screen Transitions > Nested Windows
```

---

## 3. Screen Specifications

### 3.1 Search + Live Preview (Default Screen)

```
 RECON ──────────────────────────────────────────────────
 "sulfide electrolyte solid state battery" | 47 | 1.2s

 RESULTS                              LIVE PREVIEW
 ───────────────────────────────────────────────────────
                                      Tesla Inc ● 82%
  NAME        SCORE   AGE
  ───────────────────                  ┌─ Info ─ Claims ─ Image ─┐
> 1 US23-45678  82%   2y             │                          │
  2 CN22-12345  78%   3y             │  Solid-State Battery     │
  3 EP23-78901  81%   2y             │  with Sulfide Electrolyte│
  4 JP22-56789  76%   3y             │                          │
  5 US23-11111  75%   2y             │  Assignee: Tesla Inc     │
  6 WO23-22222  74%   2y             │  Inventors: J. Smith,    │
  ...                                │  A. Lee, R. Kumar        │
                                     │  Filed: 2023-03-15       │
                                     │  Expires: 2043-03-15     │
                                     │  Family: 5 patents       │
                                     │                          │
                                     │  [Figure 1 inline]       │
                                     │  ┌────────────────┐      │
                                     │  │▓▓▓▓▓▓▓▓░░░░▓▓│      │
                                     │  │▓▓░░░░░░▓▓░░▓▓▓│      │
                                     │  │▓▓░░░░░░▓▓░░▓▓▓│      │
                                     │  │▓▓▓▓▓▓▓▓░░░░▓▓│      │
                                     │  └────────────────┘      │
                                     │  Cathode | Electrolyte   │
                                     │                          │
                                     │  Score: 82/100           │
                                     │  ████████████████████░░  │
                                     │  NIH●●●●● SEC●●●●○ DOE○  │
                                     │                          │
                                     │  [d]ownload  [s]ave      │
                                     │  [r]ead full  [o]pen     │
                                     └──────────────────────────┘

 ───────────────────────────────────────────────────────
 ↑↓nav  Enter:detail  h/l:tab  /filter  s:save  e:export  q:quit
```

**Behaviors:**
- `↑/↓` navigates results, preview updates instantly (<100ms)
- `h/l` or `←/→` switches preview tab (Info → Claims → Image)
- `Enter` opens full detail view
- `1-9,0` quick-opens result
- `/` filters within results
- `p` toggles three-pane layout
- Inline figure renders in **Info tab by default** (not hidden behind Image tab)

---

### 3.2 Detail View (Full Screen)

```
 RECON ── FULL DETAIL ── US2023-45678 ───────────────────
 Tesla Inc | ACTIVE | Expires 2043-03-15 | Family: 5

 ABSTRACT
 ───────────────────────────────────────────────────────
 A solid-state battery comprising a sulfide-based solid
 electrolyte layer disposed between a cathode and anode...

 [t]ranslated from original Chinese by DeepSeek 7B

 CLAIMS                              FIGURES
 ───────────────────────────────────────────────────────
 1. A battery cell comprising...    ┌────────────────────────┐
 2. The cell of claim 1...          │ [FIGURE 1]             │
 3. The electrolyte of claim 2...   │ ┌────────────────────┐ │
 ...                                │ │ ▓▓▓▓▓▓▓▓░░░░▓▓▓▓▓▓│ │
                                    │ │ ▓▓░░░░░░▓▓░░▓▓░░░░│ │
                                    │ │ ▓▓░░░░░░▓▓░░▓▓░░░░│ │
                                    │ │ ▓▓▓▓▓▓▓▓░░░░▓▓▓▓▓▓│ │
                                    │ └────────────────────┘ │
                                    │ [1●] [2] [3] [4]       │
                                    └────────────────────────┘

 INTELLIGENCE                      ARBITRAGE
 ───────────────────────────────────────────────────────
 NIH RePORTER                      US: ACTIVE (expires 2043)
 • Dr. J. Smith, $1.2M            EP: ACTIVE (expires 2044)
   "Advanced Sulfide Electrolytes" CN: ACTIVE (expires 2044)
   2021-2024                      JP: NOT FILED
                                  KR: ACTIVE (expires 2044)
 SEC EDGAR                         Compulsory: None detected
 • Tesla 10-K Q3 2023            Licensing: None detected
   "sulfide-based solid-state
   cells in R&D pipeline"

 OpenAlex
 • 3 citing papers from MIT
 • 1 paper from Stanford

 ───────────────────────────────────────────────────────
 <Esc>back  <s>ave  <d>ownload  <e>xport  <o>pen external
 <c>itations  <a>rbitrage  <f>amily tree  <?>help
```

---

### 3.3 Reader Mode (Full Screen, No Chrome)

```
 RECON ── READER ── US2023-45678 ────────────────────────
 Tesla Inc | 12 claims | 4 figures | ~8 min read

 ABSTRACT
 ───────────────────────────────────────────────────────
 A solid-state battery comprising a sulfide-based solid
 electrolyte layer disposed between a cathode and anode...

 CLAIM 1 (Independent)
 ───────────────────────────────────────────────────────
 A battery cell comprising:
   a) a cathode layer comprising lithium nickel manganese
      cobalt oxide;
   b) an anode layer comprising lithium metal;
   c) a solid electrolyte layer disposed between said
      cathode and anode, wherein said electrolyte comprises
      lithium sulfide and at least one lithium halide.

 [Figure 1 reference: cross-sectional view showing layers
  10, 20, 30 as described above]

 CLAIM 2 (Dependent)
 ───────────────────────────────────────────────────────
 The battery cell of claim 1, wherein said solid electrolyte
 layer has a thickness of less than 50 micrometers.

 ───────────────────────────────────────────────────────
 Line 23 of 156 | Claim 1 of 12 | [↑↓]scroll [c]laims [f]igures
 [d]ownload [s]ave [Esc]back
```

**Rules:**
- No Header, no Footer, no result list
- Full terminal width for content
- Minimal status line at bottom
- `q` or `Escape` returns to search
- `j/k` scrolls claims

---

### 3.4 Image Gallery (Image Tab Expanded)

```
 RECON ── IMAGE GALLERY ── US2023-45678 ─────────────────
 Tesla Inc ● 4 figures

 ┌─ Info ─ Claims ─[Image]──────────────────────────────┐
 │                                                       │
 │  FIGURE 1 OF 4                                        │
 │  Battery Cross-Sectional View                         │
 │                                                       │
 │  ┌────────────────────────────────────────────┐       │
 │  │                                            │       │
 │  │         [INLINE KITTY RENDER]              │       │
 │  │                                            │       │
 │  │     Cathode (10)      Anode (30)           │       │
 │  │     Electrolyte (20)                       │       │
 │  │                                            │       │
 │  │  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]  │       │
 │  │  [▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓]  │       │
 │  │  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]  │       │
 │  │                                            │       │
 │  └────────────────────────────────────────────┘       │
 │                                                       │
 │  ┌──┐ ┌──┐ ┌──┐ ┌──┐                                  │
 │  │1●│ │2 │ │3 │ │4 │  ← thumbnail strip               │
 │  └──┘ └──┘ └──┘ └──┘                                  │
 │                                                       │
 │  [n]ext fig [p]rev fig [f]ullscreen [o]pen external   │
 │  [d]ownload figure [c]opy caption                     │
 │                                                       │
 │  Caption: Cross-sectional view of solid-state         │
 │  battery cell showing layer structure.                │
 │                                                       │
 └───────────────────────────────────────────────────────┘
```

---

### 3.5 Help Overlay (Inline, Not Modal)

```
 RECON ──────────────────────────────────────────────────
 "sulfide electrolyte" | 47 results

 RESULTS                              PREVIEW
 ───────────────────────────────────────────────────────
  ... (background slightly dimmed)     ...
                                       ┌─ Help Overlay ─┐
                                       │                │
                                       │  NAVIGATION    │
                                       │  ↑↓ j/k  Navigate results   │
                                       │  Enter   Open detail        │
                                       │  h/l     Switch tab         │
                                       │  1-9     Quick-open         │
                                       │                │
                                       │  ACTIONS       │
                                       │  s  Save to collection      │
                                       │  e  Export collection       │
                                       │  d  Download patent         │
                                       │  r  Reader mode             │
                                       │  f  Toggle figure view      │
                                       │  t  Translate               │
                                       │                │
                                       │  SEARCH        │
                                       │  /  Filter results          │
                                       │  ?  Toggle this help        │
                                       │  q  Quit                    │
                                       │                │
                                       │  [?] Close  [Esc] Dismiss   │
                                       └────────────────┘
```

**Rules:**
- Inline `Static` widget, NOT `ModalScreen`
- Toggle with `?` key
- Background slightly dimmed (CSS opacity)
- `Escape` or `?` dismisses

---

### 3.6 Terminal Detection Popup (First Run)

```
┌─ RECON ─────────────────────────────────────────────┐
│                                                       │
│  Terminal Detection                                   │
│                                                       │
│  Your terminal: Terminal.app                          │
│  Inline images: ❌ Not supported                      │
│                                                       │
│  Options:                                             │
│                                                       │
│  [●] Use external viewer (recommended)                │
│      Press 1-9 to select figure, opens in Preview/feh │
│                                                       │
│  [ ] Switch to supported terminal                     │
│      Kitty, iTerm2, WezTerm, or Ghostty               │
│      https://github.com/kovidgoyal/kitty              │
│                                                       │
│  [ ] Continue without images                          │
│      Text-only mode, figure captions only             │
│                                                       │
│  [?] Learn more about terminal image protocols        │
│  [Enter] Confirm  [q] Quit                            │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 4. Keyboard Map (Complete)

| Key | Context | Action |
|-----|---------|--------|
| `↑/↓` or `j/k` | Results | Navigate |
| `Enter` | Results | Full detail |
| `h/l` or `←/→` | Preview | Switch tab (Info/Claims/Image) |
| `1-9,0` | Results | Quick-open result |
| `/` | Results | Filter within results |
| `p` | Results | Toggle three-pane layout |
| `f` | Detail/Image | Toggle figure view |
| `t` | Detail/Claims | Translate |
| `r` | Results/Detail | Reader mode |
| `s` | Anywhere | Save to collection |
| `d` | Anywhere | Download patent |
| `e` | Anywhere | Export collection |
| `o` | Preview/Image | Open figure in external viewer |
| `n/p` | Image tab | Next/previous figure |
| `1-9` | Image tab | Jump to figure N |
| `i` | Claims | Toggle independent claims only |
| `c` | Detail | Citation graph |
| `a` | Detail | Arbitrage status |
| `m` | Anywhere | Toggle synthesis mode |
| `?` | Anywhere | Help overlay |
| `q` / `Esc` | Anywhere | Back / Quit |

---

## 5. Feature Specifications

### 5.1 Patent Meta-Search
- Query USPTO, EPO, WIPO, Google Patents, Lens.org simultaneously
- Return merged, deduplicated results
- Sort descending by score, never remove entries
- Missing data flagged as `[?]` or `UNKNOWN`

### 5.2 Live Preview
- Results list + preview pane
- Preview updates in <100ms on navigation (no Enter required)
- Three tabs: Info, Claims, Image

### 5.3 Image Handling
- **Primary:** Kitty graphics protocol
- **Secondary:** iTerm2 inline images
- **Tertiary:** Sixel
- **Fallback:** External viewer (xdg-open/open/start)
- Auto-detect terminal capability on startup
- Cache converted PNGs

### 5.4 Cross-Reference Intelligence
- Correlate with NIH, NSF, SEC, OpenAlex, arXiv, OpenCorporates
- Equal-weight scoring: +20 per signal, max 100
- Three-tier name matching: exact > fuzzy > co-occurrence
- Display raw matching strings + confidence percentages

### 5.5 Score Algorithm
```
Base: 0
Per signal found: +20 (max 100)

Signals:
1. Grant funding (NIH/NSF/DOE)
2. Corporate filing (SEC 10-K/8-K)
3. Academic citation (OpenAlex/arXiv)
4. Temporal proximity (filing within 2yr of grant)
5. Supply chain evidence

Penalties (applied after sum):
- Abandoned status: -30
- Shell company detected: -20

Sort: Descending by final score. Never remove entries.
```

### 5.6 Rate Limiting
- USPTO: 76/min (24% headroom)
- EPO: 3.04/sec (24% headroom)
- WIPO: 76/day (24% headroom)
- Auto-backoff on 429: 1s→2s→4s→8s→graceful fail

### 5.7 Cache Strategy
- Document content: cache indefinitely
- Status metadata: refresh every 30 days
- Citations: append-only
- Family links: refresh every 30 days

### 5.8 Save & Export
- Save to named collections (SQLite)
- Export formats: PDF, Markdown, JSON, BibTeX, CSV
- Reader mode: full-screen text view

---

## 6. Technical Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.12+ |
| TUI Framework | Textual | Latest |
| HTTP Client | httpx | Latest |
| Image Conversion | Pillow | Latest |
| Image Render | kitty-img / img2sixel | Protocol-native |
| Fuzzy Match | rapidfuzz | Latest |
| CLI Framework | typer | Latest |
| Cache | SQLite | stdlib |
| Config | tomli / tomli-w | stdlib |

### Dependencies (Minimal)
```
textual
httpx
Pillow
rapidfuzz
typer
fpdf2
```

### Prohibited Dependencies
- Pydantic (use stdlib dataclasses)
- SQLAlchemy (use sqlite3)
- openai / anthropic / ollama (Zero-AI default)
- tkinter / PyQt / webbrowser (no GUI fallback)

---

## 7. Error Voice Specification

| Scenario | Correct Voice | Incorrect Voice |
|----------|--------------|-----------------|
| API timeout | `ERR: USPTO timeout. Retrying in 4s.` | "Oops! Something went wrong." |
| Rate limit | `ERR: Source [Lens] rate limit exceeded. Provide API key.` | "Please try again later." |
| Partial results | `3 of 5 sources responded. Results partial.` | "Failed to load." |
| Unsupported terminal | `ERR: Image rendering unsupported. Action: Open externally.` | "Your terminal is not supported." |
| Missing data | `[?]` or `UNKNOWN` | Hidden or guessed |

---

## 8. Mode Specifications

### Zero-AI Mode (Default)
- Rule-based correlation
- Template output
- Fast, deterministic, debuggable
- Slightly more cognitive load on user

### Local AI Mode (Optional Toggle)
- Ollama + DeepSeek 7B/14B
- Natural language synthesis
- 8-16GB RAM required
- ~15s per synthesis

### Remote AI Mode (Optional Toggle)
- User-provided API key
- Per-request cost
- Network dependent

---

## 9. Data Sources

| Source | Data | Endpoint | Auth |
|--------|------|----------|------|
| USPTO | Full text, claims, images | developer.uspto.gov | API key (free) |
| EPO | EP patents, families | ops.epo.org | OAuth (free) |
| WIPO | International filings | patentscope.wipo.int | None |
| Google Patents | Prior art, citations | Unofficial | None |
| Lens.org | Citation graphs | api.lens.org | API key (free) |
| NIH RePORTER | Grants | api.reporter.nih.gov | None |
| NSF | Awards | nsf.gov/awardsearch | None |
| SEC EDGAR | Filings | sec.gov/Archives | None |
| OpenAlex | Papers | api.openalex.org | None |
| arXiv | Preprints | export.arxiv.org | None |
| OpenCorporates | Companies | api.opencorporates.com | Free tier |

---

## 10. Testing Requirements

- **Test-first enforcement:** Write failing tests before implementation
- **37 tests minimum** covering all phases
- **Mock external APIs** for unit tests
- **Integration tests** with recorded HTTP responses
- **TUI tests** using Textual's async pilot framework

---

## 11. Git Commit Strategy

```
chore: add .gitignore
docs: add Spec Kit constitution and specification
feat: Phase 1 — Foundation
feat: Phase 2 — Core Patent Search & Navigation
feat: Phase 3 — Three-Tab Preview & Image Rendering
feat: Phase 4 — Cross-Reference Intelligence
feat: Phase 5 — Collections, Export & Reader Mode
polish: Phase 6 — Constitution Verification & Final Audit
feat: v0.2.0 — Live Patent API Integration
fix: TUI tab switching — replace get_item_at with children[index]
```

---

## 12. Known Limitations (v0.2.0)

- USPTO requires API key for live data
- WIPO returns 403 without proper auth
- EPO has TODO for real OPS implementation
- Google Patents and Lens use mock data in test mode
- Non-English patents need translation toggle (v0.3.0)
- Citation graph visualization not yet implemented (v0.3.0)

---

## 13. Next Version Roadmap

### v0.3.0
- EPO OAuth implementation
- Non-English patent translation (Ollama + DeepSeek)
- Citation graph ASCII visualization
- Real API key testing and validation

### v0.4.0
- Advanced adversarial detection
- Supply chain tracing integration
- Network mapping (inventor/institution graphs)

---

*This document is the single source of truth for RECON's design. All implementation must conform to the Constitution and specifications herein.*
