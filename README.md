# RECON — Terminal-Native Patent Research Tool

**RECON** is a keyboard-first, terminal-native patent research tool. It aggregates patent data from multiple sources (USPTO, PatSnap, Google Patents, WIPO, Lens.org, EPO), presents results in a clean TUI or CLI, and provides scoring, citation graphs, export, and optional local-AI translation.

## Features

- **Multi-source search** — USPTO API, PatSnap API, Google Patents scraping, WIPO/Lens/EPO via DuckDuckGo + BeautifulSoup
- **Source filtering** — Include/exclude sources via CLI `--source` or TUI `S` overlay
- **Signal scoring** — Equal-weight 20-point signals (government grants, corporate investment, academic research, temporal recency, news/media)
- **Live preview** — Three-tab detail pane (Info / Claims / Image) with keyboard navigation
- **Citation graph** — ASCII tree view of forward/backward citations (scraped from Google Patents or mock data)
- **Export** — JSON, CSV, BibTeX, Markdown, PDF
- **Translation** — Optional local translation via Ollama (opt-in, Zero-AI default)
- **Terminal-native** — No GUI, no Electron, no modal dialogs

## Installation

### Via PyPI (recommended)

```bash
pipx install recon-patent
```

### Via GitHub

```bash
pipx install git+https://github.com/anubhavaanand/recon.git
```

Ensure `~/.local/bin` is in your `PATH`.

### Via install script (hacker method)

```bash
curl -sSL https://raw.githubusercontent.com/anubhavaanand/recon/main/install.sh | bash
```

### Via pip

```bash
pip install recon-patent
```

### From source

```bash
git clone https://github.com/anubhavaanand/recon.git
cd recon
pip install -e .
```

### Development

```bash
pip install -e ".[test,dev]"
```

## Quick Start

### Launch the interactive TUI

```bash
recon
```

Type a query (e.g. `solid state battery`) and press Enter. Navigate results with `j`/`k`, open detail with Enter, switch tabs with `h`/`l`.

### CLI search

```bash
recon search "sulfide electrolyte"
```

Filter by source:

```bash
recon search "quantum battery" --source uspto,patsnap,google
```

### End-to-end run with export

```bash
recon run "lithium anode" --export json
```

### View saved collection

```bash
recon collection list
recon collection clear
```

### Manage API keys

```bash
recon config show
recon config set --patsnap-key YOUR_KEY
recon config test
```

### Export collection

```bash
recon export --format csv
```

Formats: `json`, `csv`, `bibtex`, `markdown`, `pdf`.

## TUI Key Bindings

| Key | Action |
|-----|--------|
| `↑`/`↓` `j`/`k` | Navigate results |
| `Enter` | Open detail view |
| `h`/`l` or `←`/`→` | Switch preview tab |
| `/` | Focus search input |
| `s` | Save patent to collection |
| `e` | Export collection overlay |
| `S` | Source filter overlay |
| `c` | Toggle citation graph |
| `t` | Toggle translation |
| `r` | Reader mode |
| `m` | Synthesis mode |
| `?` | Help overlay |
| `q` / `Esc` | Back / Quit |

## Architecture

```
recon/
├── cli/                 — Typer CLI (main: search/run/config/collection, export, download)
├── core/
│   ├── models.py        — PatentRecord, CrossReference dataclasses
│   ├── search.py        — Multi-source search orchestration + GP enrichment + source filtering
│   ├── enrichment.py    — Cross-reference intelligence (NIH/NSF/DOE/SEC/arXiv/OpenAlex)
│   ├── scoring.py       — Signal scoring (equal-weight algorithm)
│   ├── metrics.py       — Scoring metrics & contribution breakdown
│   ├── arbitrage.py     — Arbitrage status calculation
│   ├── citations.py     — Citation graph fetching (Google Patents scrape)
│   ├── translation.py   — Local Ollama translation with cache
│   ├── intelligence.py  — Signal aggregation helpers
│   ├── ai.py            — Opt-in local AI (synthesis mode)
│   └── config.py        — Config management (~/.config/recon/config.toml)
├── clients/
│   ├── patent_apis.py   — USPTO, EPO, WIPO, Lens, Google Patents API clients
│   ├── scrapers.py      — Keyless DDG + Google Patents XHR scraping & enrichment
│   ├── base.py          — BaseAsyncClient with rate-limit + backoff
│   ├── base_scraper.py  — Shared scraping plumbing
│   └── circuit_breaker.py — Per-source failure isolation
├── tui/
│   ├── app.py           — Textual App, Tokyo Night theme, light/dark autodetect
│   ├── screens.py       — SearchScreen, DetailScreen, ReaderModeScreen, etc.
│   └── widgets/         — ResultList, Info/Claims/Image tabs, CitationTree,
│                          CommandPalette, AlertBanner, Sixel/Kitty image rendering
├── storage/
│   ├── cache.py         — SQLite cache (search results, collection, translations)
│   └── migrate.py       — Schema migrations
└── tests/               — 262 tests (pytest)
```

The full design history — original interface mockup, constitution, and every accepted
decision — lives in [docs/DESIGN_HISTORY.md](docs/DESIGN_HISTORY.md).

## Configuration

Keys are stored in `~/.config/recon/config.toml` (chmod 600):

| Variable | Source | Required |
|----------|--------|----------|
| `PATSNAP_API_KEY` | PatSnap | No (scraper fallback exists for most features) |
| `USPTO_API_KEY` | USPTO | No |
| `EPO_CONSUMER_KEY` / `EPO_CONSUMER_SECRET` | EPO | No (scraper fallback exists) |
| `LENS_API_KEY` | Lens.org | No (scraper-only) |

Set via `recon config set` (interactive) or `.env` file.

## Translation (Ollama)

RECON can optionally translate non-English patent abstracts using a local Ollama instance:

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3

# RECON auto-detects non-English text and uses Ollama
# Press t in the TUI to toggle translation
```

When Ollama is not running, RECON gracefully displays the original text.

## Testing

```bash
pip install -e ".[test]"
pytest
```

## License

MIT
