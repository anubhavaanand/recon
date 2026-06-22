<p align="center">
  <img src="https://raw.githubusercontent.com/anubhavaanand/recon/main/assets/logo.png" alt="RECON" width="120">
</p>

<h1 align="center">RECON</h1>

<p align="center">
  <strong>Terminal-native patent research for technology builders.</strong><br>
  Meta-search across USPTO, EPO, WIPO, and Google Patents. Zero-AI by default. Keyboard-first. Deterministic.
</p>

<p align="center">
  <a href="https://github.com/anubhavaanand/recon/actions/workflows/ci.yml">
    <img src="https://github.com/anubhavaanand/recon/workflows/CI/badge.svg" alt="Build Status">
  </a>
  <a href="https://github.com/anubhavaanand/recon/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
  </a>
  <a href="https://github.com/anubhavaanand/recon/releases">
    <img src="https://img.shields.io/github/v/release/anubhavaanand/recon?include_prereleases" alt="Version">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python 3.12+">
  </a>
  <a href="https://github.com/anubhavaanand/recon/blob/main/.specify/docs/constitution.md">
    <img src="https://img.shields.io/badge/constitution-zero--AI%20default-green" alt="Constitution: Zero-AI Default">
  </a>
</p>

---

## Table of Contents

- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation & Local Setup](#installation--local-setup)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features

- **Multi-source patent search** — Query USPTO, EPO, WIPO, Google Patents, and Lens.org simultaneously via `asyncio.gather`
- **Terminal-native TUI** — Built with [Textual](https://textual.textualize.io/); runs in any modern terminal (Kitty, iTerm2, WezTerm, Ghostty, Alacritty)
- **Inline image rendering** — Patent diagrams displayed via Kitty graphics protocol, iTerm2 inline images, or Sixel fallback
- **Cross-reference intelligence** — Automatic correlation with NIH, NSF, SEC, OpenAlex, arXiv, and OpenCorporates using deterministic `rapidfuzz` scoring
- **Zero-AI by default** — All scoring is deterministic (+20 per signal, max 100). Optional AI toggles for future versions
- **Collections & export** — Save patents to local SQLite collections; export to CSV, JSON, BibTeX, Markdown, or PDF
- **Reader mode** — Distraction-free full-width patent reading with `r` hotkey
- **24% rate limit headroom** — Automatic backoff (1s → 2s → 4s → 8s) with concurrent API respect
- **30-day search cache** — SQLite-backed with SHA256 query hashing; warm cache responses < 100ms
- **Keyboard-first navigation** — No mouse required. Every action has a hotkey

---

## Tech Stack

| Layer | Technology | Purpose | Version |
|-------|-----------|---------|---------|
| **Language** | Python | Runtime | 3.12+ |
| **TUI Framework** | [Textual](https://textual.textualize.io/) | Terminal UI | ^0.52 |
| **HTTP Client** | [httpx](https://www.python-httpx.org/) | Async API calls | ^0.27 |
| **Image Processing** | [Pillow](https://pillow.readthedocs.io/) | Patent diagram rendering | ^10.0 |
| **Fuzzy Matching** | [rapidfuzz](https://maxbachmann.github.io/RapidFuzz/) | Entity correlation | ^3.0 |
| **CLI Framework** | [typer](https://typer.tiangolo.com/) | Command-line interface | ^0.12 |
| **PDF Generation** | [fpdf2](https://py-pdf.github.io/fpdf2/) | Export formatter | ^2.7 |
| **Database** | SQLite (stdlib) | Local cache & collections | 3.39+ |
| **Config** | TOML | API key storage | tomli / tomli-w |

**Explicitly NOT used:** No Pydantic, no SQLAlchemy, no Docker, no Kubernetes, no web server, no cloud dependencies. See [Constitution](.specify/docs/constitution.md) for rationale.

---

## Prerequisites

- **Python 3.12+** — Check with `python3 --version`
- **Terminal with Unicode support** — Any modern terminal emulator
- **For inline images:** Kitty, iTerm2, WezTerm, or Ghostty recommended (Sixel fallback available)
- **API keys (optional):** USPTO, EPO, and Lens.org keys unlock live data. WIPO and Google Patents work without keys

---

## Installation & Local Setup

### Option A: Install from PyPI (Recommended)

```bash
pip install recon-patent
```

### Option B: Install from Source

```bash
# 1. Clone the repository
git clone https://github.com/anubhavaanand/recon.git
cd recon

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode
pip install -e ".[test]"

# 4. Verify installation
recon --help
```

### Option C: Using uv (Fastest)

```bash
# 1. Clone
git clone https://github.com/anubhavaanand/recon.git
cd recon

# 2. Install with uv
uv pip install -e ".[test]"

# 3. Verify
recon --help
```

---

## Quick Start

### 1. Configure API Keys (Optional but Recommended)

```bash
# USPTO — free registration at https://developer.uspto.gov/
recon config set --uspto-key YOUR_USPTO_KEY

# EPO — free registration at https://developers.epo.org/
recon config set --epo-consumer-key YOUR_EPO_KEY --epo-consumer-secret YOUR_EPO_SECRET

# Lens.org — free tier at https://www.lens.org/lens/user/subscriptions
recon config set --lens-key YOUR_LENS_KEY

# Verify configuration
recon config show
```

> **Note:** WIPO and Google Patents do not require API keys.

### 2. Search Patents (CLI Mode)

```bash
# Quick search with rich table output
recon search "solid state battery"

# Limit results
recon search "semiconductor packaging" --limit 10

# Search specific sources only
recon search "CRISPR gene editing" --sources uspto,wipo
```

### 3. Search Patents (TUI Mode)

```bash
# Launch interactive terminal UI
recon search
```

Inside the TUI:
- Type your query and press **Enter**
- Navigate results with **↑ / ↓**
- Switch tabs with **Tab** or **l / h** (Info → Claims → Image)
- Save to collection with **s**
- Open reader mode with **r**
- Export with **e**
- Toggle help with **?**
- Quit with **q**

### 4. Export Collections

```bash
# Export saved patents to various formats
recon export --format json
recon export --format csv
recon export --format bibtex
recon export --format markdown
recon export --format pdf

# Specify output file
recon export --format json --output my_research.json
```

### 5. Cache Management

```bash
# Cache is automatic, but you can inspect it
ls -la ~/.cache/recon/

# Cache entries expire after 30 days
# Force fresh search with --no-cache (if implemented)
```

---

## Environment Variables

RECON does **not** use environment variables for configuration. All settings are stored in `~/.config/recon/config.toml` with `0600` permissions. This avoids credential leakage via `/proc/*/environ`, shell history, or `ps` output.

| **Variable** | **Description** | **Required** | **Default** | **Set Via** |
|--------------|-----------------|--------------|-------------|-------------|
| `RECON_CONFIG_DIR` | Override config directory path | No | `~/.config/recon/` | `recon config set` or manual edit |
| `RECON_CACHE_DIR` | Override cache directory path | No | `~/.cache/recon/` | Not exposed — hardcoded |
| `TERM` | Terminal type detection | Auto-detected | `$TERM` | Environment |
| `TERM_PROGRAM` | Terminal program detection | Auto-detected | iTerm.app, etc. | Environment |
| `KITTY_WINDOW_ID` | Kitty graphics protocol detection | Auto-detected | — | Environment |
| `COLORFGBG` | Light/dark mode detection | Auto-detected | — | Environment |

> **Note:** No `API_KEY`, `SECRET`, or `PASSWORD` variables exist. All secrets are file-based with Unix permissions.

---

## Keyboard Shortcuts

### Global

| Key | Action | Context |
|-----|--------|---------|
| `q` | Quit | Anywhere |
| `?` | Toggle help overlay | Anywhere |
| `/` | Focus search input | SearchScreen |

### SearchScreen

| Key | Action |
|-----|--------|
| `↑ / ↓` | Navigate results |
| `Enter` | Select / preview patent |
| `Tab / l` | Next tab (Info → Claims → Image) |
| `Shift+Tab / h` | Previous tab |
| `s` | Save to collection |
| `e` | Export collection |
| `d` | Download patent (queued) |
| `r` | Open reader mode |
| `c` | Citation graph (v0.3.0) |

### ReaderModeScreen

| Key | Action |
|-----|--------|
| `q` | Quit reader mode |
| `j / k` | Scroll down / up |
| `Escape` | Return to search |

---

## Running Tests

```bash
# Run all tests
cd ~/Projects/recon
source .venv/bin/activate
pytest -xvs

# Run specific test file
pytest tests/test_search.py -xvs

# Run with coverage
pytest --cov=recon --cov-report=html

# Run performance benchmarks
pytest tests/test_performance.py -v

# Run security audit
pytest tests/test_error_handling.py -v
```

### Test Coverage

| Suite | Tests | Purpose |
|-------|-------|---------|
| `test_models.py` | 3 | Dataclass validation |
| `test_cache.py` | 3 | SQLite operations, TTL |
| `test_client.py` | 2 | Backoff, retry logic |
| `test_search.py` | 2 | Descending sort, deduplication |
| `test_patent_apis.py` | 5 | Mock API clients (USPTO, EPO, WIPO, Lens, Google) |
| `test_scoring.py` | 2 | rapidfuzz matching, equal-weight scoring |
| `test_export.py` | 7 | CSV, JSON, BibTeX, Markdown, PDF formats |
| `test_lazy_loading.py` | 2 | Claims/image lazy load |
| `test_terminal_protocols.py` | 2 | Kitty, iTerm2 detection |
| `test_tui_navigation.py` | 9 | Keyboard bindings, help overlay |
| `test_integration_new.py` | 2 | End-to-end with mocked APIs |
| **Total** | **37** | **All passing** |

---

## Deployment

RECON is **not deployed as a service**. It is a local CLI/TUI application distributed via:

| Method | Command | Audience |
|--------|---------|----------|
| **PyPI** | `pip install recon-patent` | End users |
| **GitHub Releases** | Download `.whl` or `.tar.gz` | End users |
| **Source** | `git clone` + `pip install -e .` | Contributors |
| **AUR** | `yay -S recon-patent` | Arch Linux users (future) |
| **Homebrew** | `brew install recon` | macOS users (future) |

### Release Checklist

```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Run full test suite
pytest -xvs

# 4. Build distribution
python -m build

# 5. Upload to PyPI
python -m twine upload dist/*

# 6. Create GitHub release
git tag v0.2.0
git push origin v0.2.0
```

---

## API Reference

RECON is a CLI/TUI application, not a web service. However, the internal Python API is documented for contributors and power users.

### Core Modules

| Module | Classes / Functions | Purpose |
|--------|---------------------|---------|
| `core.models` | `PatentRecord`, `CrossReference` | Data structures |
| `core.search` | `search_patents()`, `sort_and_merge_results()` | Search orchestration |
| `core.scoring` | `ScoreEngine`, `match_entities()` | Deterministic scoring |
| `clients.base` | `BaseClient`, `RateLimit`, `TokenBucket` | HTTP client with backoff |
| `clients.patent_apis` | `USPTOClient`, `EPOClient`, `WIPOClient`, etc. | API adapters |
| `storage.cache` | `CacheDatabase` | SQLite cache & collections |
| `tui.app` | `ReconApp` | Textual application entry |
| `tui.screens` | `SearchScreen`, `ReaderModeScreen` | TUI screens |
| `cli.main` | `app` (Typer) | CLI entrypoint |

### Full Documentation

- **Architecture:** [RECON_Technical_Architecture_Document_v1.0.0.md](docs/RECON_Technical_Architecture_Document_v1.0.0.md)
- **Database Design:** [RECON_Database_Design_v1.0.0.md](docs/RECON_Database_Design_v1.0.0.md)
- **Security:** [RECON_Security_Access_Control_Document_v1.0.0.md](docs/RECON_Security_Access_Control_Document_v1.0.0.md)
- **Constitution:** [.specify/docs/constitution.md](.specify/docs/constitution.md)
- **PRD:** [RECON_PRD_v1.0.0_Final.md](docs/RECON_PRD_v1.0.0_Final.md)

---

## Contributing

RECON follows the [RECON Constitution](.specify/docs/constitution.md). All contributions must respect:

1. **Zero-AI default** — No AI/ML components in core path
2. **Minimal dependencies** — Only add if absolutely necessary
3. **Terminal-native** — No GUI fallbacks, no web interfaces
4. **Keyboard-first** — Every feature must be accessible via hotkey
5. **Dry error voice** — `ERR:` prefix, actionable, no stacktraces in standard output
6. **Deterministic scoring** — Equal weights, transparent signals

### Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/recon.git
cd recon

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dev dependencies
pip install -e ".[test]"

# 4. Create branch
git checkout -b feature/your-feature-name

# 5. Make changes, run tests
pytest -xvs

# 6. Commit with phase-based messages
git commit -m "feat: add your feature description"

# 7. Push and open PR
git push origin feature/your-feature-name
```

### Commit Message Convention

```
feat: add new feature
fix: fix bug in feature
docs: update documentation
style: formatting, no code change
refactor: code restructuring
test: add or update tests
chore: build process, dependencies
security: security-related changes
```

### Code Review Criteria

- [ ] All tests pass (`pytest -xvs`)
- [ ] No new dependencies without justification
- [ ] Error messages use `ERR:` prefix
- [ ] No `print()` without `INFO:` or `ERR:` prefix
- [ ] No `except Exception: pass` patterns
- [ ] Keyboard shortcuts documented in help overlay
- [ ] Constitution compliance verified

---

## License

[MIT](LICENSE) © Anubhav Anand

```
MIT License

Copyright (c) 2026 Anubhav Anand

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Built with patience for terminal dwellers.<br>
  <a href="https://github.com/anubhavaanand/recon">github.com/anubhavaanand/recon</a>
</p>
