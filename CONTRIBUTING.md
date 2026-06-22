# Contributing to RECON

> **Thank you for considering a contribution to RECON.**
> This project is maintained by a solo developer with community support. Every issue report, bug fix, feature suggestion, and documentation improvement is valued. You do not need to be a patent law expert or a TUI wizard to contribute — curiosity and respect for the project's philosophy are sufficient.

---

## Table of Contents

- [Project Philosophy](#project-philosophy)
- [Code of Conduct](#code-of-conduct)
- [How to Report Bugs](#how-to-report-bugs)
- [How to Suggest Features](#how-to-suggest-features)
- [Development Setup](#development-setup)
- [Branch Naming Convention](#branch-naming-convention)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Code Style & Linting](#code-style--linting)
- [Testing Requirements](#testing-requirements)
- [Definition of Done](#definition-of-done)
- [Questions?](#questions)

---

## Project Philosophy

RECON is a terminal-native patent research tool built on a strict constitution. Before contributing, please understand these non-negotiable principles:

1. **Zero-AI by default.** The core path contains no AI/ML components. All scoring is deterministic. Optional AI toggles may exist in future versions, but they must be explicitly enabled and never the default.

2. **Minimal dependencies.** We add a new dependency only when the problem cannot be solved with the standard library or existing dependencies. Every new dependency must be justified in the PR description.

3. **Terminal-native.** No GUI fallbacks. No web interfaces. No Electron. The tool lives in the terminal and respects terminal conventions.

4. **Keyboard-first.** Every feature must be accessible via keyboard. Mouse support is optional, never required.

5. **Dry, actionable error voice.** Error messages start with `ERR:`. They are concise. They never include stack traces in standard output. They tell the user what to do next.

6. **Speed over depth.** < 3 seconds for cold search. < 100ms for warm cache navigation. Lazy loading for previews. No blocking operations in the TUI event loop.

7. **Transparency.** All scoring signals are visible. No black-box algorithms. Users must understand why a patent received a given score.

8. **Equal weights.** Cross-reference scoring uses +20 per signal, max 100. No weighted averages, no ML models, no "confidence scores" without explanation.

9. **24% rate limit headroom.** We respect API providers. We back off. We cache aggressively.

10. **No modal dialogs.** All UI interactions are inline or use screen transitions. No pop-ups, no alerts, no confirmation dialogs.

If your contribution conflicts with any of these principles, it will not be merged. If you believe an exception is warranted, open an issue to discuss it before writing code.

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

In short:

- Be respectful in all interactions.
- Assume good intent.
- Welcome newcomers.
- Criticize ideas, not people.
- No harassment, discrimination, or trolling.

Violations may result in a temporary or permanent ban from the project.

To report a violation, email the maintainer directly or open a private issue if the platform supports it.

---

## How to Report Bugs

### Before You Report

1. **Search existing issues.** Your bug may already be reported or fixed in a newer version.
2. **Update to the latest version.** `pip install --upgrade recon-patent` or pull the latest `main`.
3. **Check the constitution.** The behavior you see may be intentional.

### Opening a Bug Report

Use the **Bug Report** issue template. If the template is unavailable, include:

| Field | Description | Example |
|-------|-------------|---------|
| **RECON version** | Output of `recon --version` | `0.2.0` |
| **Python version** | Output of `python3 --version` | `3.12.4` |
| **OS / Terminal** | Your operating system and terminal emulator | `Arch Linux / Kitty 0.35` |
| **Steps to reproduce** | Numbered list, starting from a fresh terminal | See below |
| **Expected behavior** | What you thought would happen | "Claims tab should show patent claims" |
| **Actual behavior** | What actually happened | "Claims tab is empty" |
| **Error message** | Full terminal output, if any | `AttributeError: 'ResultList' object has no attribute 'get_item_at'` |
| **Minimal reproduction** | The smallest command or code that triggers the bug | `recon search` then press `l` |

### Example Bug Report

```markdown
**Version:** 0.2.0
**Python:** 3.12.4
**OS/Terminal:** Arch Linux / Kitty 0.35

**Steps to reproduce:**
1. Run `recon search`
2. Type "solid state battery" and press Enter
3. Press Down to select first result
4. Press `l` to switch to Claims tab

**Expected:** Claims tab shows patent claims text.

**Actual:** Claims tab is empty. No error message.

**Error:** None visible.

**Minimal reproduction:** `recon search` -> Enter query -> Down -> `l`
```

### What Happens Next

- The maintainer will acknowledge the issue within 48 hours.
- If reproducible, it will be labeled `confirmed` and assigned a priority.
- If more information is needed, the `needs-info` label will be applied.
- You may be asked to test a fix before it is merged.

---

## How to Suggest Features

### Before You Suggest

1. **Check the roadmap.** See [RECON_PRD_v1.0.0_Final.md](docs/RECON_PRD_v1.0.0_Final.md) for planned features.
2. **Check the constitution.** Features that violate the 10 principles will not be accepted.
3. **Consider scope.** RECON is a patent research tool, not a general-purpose document manager.

### Opening a Feature Request

Use the **Feature Request** issue template. If unavailable, include:

| Field | Description | Example |
|-------|-------------|---------|
| **Problem** | What pain point does this solve? | "I need to compare two patents side-by-side" |
| **Proposed solution** | How should it work? | "Add a split-screen diff mode with `d` hotkey" |
| **Alternatives considered** | What else did you try? | "Exporting both and using `diff` manually" |
| **Constitution impact** | Does this violate any principle? | "No — keyboard-first, no modals, deterministic" |
| **Priority** | How important is this to you? | "Nice to have — I can work around it" |

### Feature Request Lifecycle

1. **Discussion** — Community feedback and maintainer assessment.
2. **Acceptance** — Label `accepted` or `declined` with rationale.
3. **Assignment** — If accepted, a contributor may claim it.
4. **Implementation** — PR opened, reviewed, merged.
5. **Release** — Included in next versioned release.

---

## Development Setup

### Prerequisites

- Python 3.12+
- Git
- A terminal emulator (Kitty, iTerm2, WezTerm, or any modern terminal)
- Optional: API keys for USPTO, EPO, Lens.org (see [README.md](README.md))

### Step-by-Step Setup

```bash
# 1. Fork the repository on GitHub
#    https://github.com/anubhavaanand/recon/fork

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/recon.git
cd recon

# 3. Add upstream remote
git remote add upstream https://github.com/anubhavaanand/recon.git

# 4. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 5. Install in editable mode with test dependencies
pip install -e ".[test]"

# 6. Verify installation
recon --help

# 7. Run tests to confirm everything works
pytest -xvs
```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Rebase your main branch
git checkout main
git rebase upstream/main

# Push updated main to your fork
git push origin main
```

---

## Branch Naming Convention

All branches must follow this prefix system. No exceptions.

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New feature | `feat/epo-oauth-client` |
| `fix/` | Bug fix | `fix/tui-tab-switching` |
| `docs/` | Documentation only | `docs/readme-typo` |
| `style/` | Formatting, no logic change | `style/black-formatting` |
| `refactor/` | Code restructuring | `refactor/cache-singleton` |
| `test/` | Test additions or fixes | `test/cache-validation` |
| `chore/` | Build, dependencies, CI | `chore/update-pytest` |
| `security/` | Security-related changes | `security/config-encryption` |
| `perf/` | Performance improvements | `perf/async-client-reuse` |

### Naming Rules

- Use kebab-case (hyphens, not underscores).
- Keep it concise but descriptive: `feat/reader-mode-scroll` not `feat/r`.
- Include an issue number if applicable: `fix/#42-tui-crash`.
- One branch per change. Do not combine unrelated fixes in a single branch.

---

## Commit Message Format

RECON uses [Conventional Commits](https://www.conventionalcommits.org/) with a project-specific scope list.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Use When | Example |
|------|----------|---------|
| `feat` | New feature | `feat(tui): add citation graph screen` |
| `fix` | Bug fix | `fix(screens): replace get_item_at with highlighted_child` |
| `docs` | Documentation only | `docs(readme): add installation instructions` |
| `style` | Formatting, no logic | `style(search): black formatting` |
| `refactor` | Code restructuring | `refactor(cache): extract query_hash helper` |
| `test` | Test additions/fixes | `test(export): add PDF empty collection test` |
| `chore` | Build, deps, CI | `chore(ci): add security scan workflow` |
| `security` | Security changes | `security(config): add AES-256-GCM encryption` |
| `perf` | Performance | `perf(client): reuse AsyncClient across requests` |

### Scopes

| Scope | Area |
|-------|------|
| `tui` | Terminal UI (screens, widgets, app) |
| `cli` | Command-line interface (main.py, export) |
| `search` | Search logic (core/search.py) |
| `cache` | SQLite cache (storage/cache.py) |
| `client` | API clients (clients/*.py) |
| `models` | Data structures (core/models.py) |
| `scoring` | Cross-reference scoring (core/scoring.py) |
| `config` | Configuration management (core/config.py) |
| `tests` | Test suite |
| `docs` | Documentation |
| `deps` | Dependencies |
| `ci` | Continuous integration |

### Examples

```bash
# Good commits
feat(tui): add help overlay with keyboard shortcuts
fix(screens): handle TabActivated event ID prefixing
refactor(cache): use aiosqlite for async SQLite access
test(search): add integration test for live USPTO API
docs(readme): update keyboard shortcut table

# Bad commits (will be rejected)
update stuff
fix bug
WIP
temp
```

### Body and Footer

Use the body to explain **why** the change was made, not just what.

```
fix(screens): replace get_item_at with highlighted_child

Textual's ListView does not have a get_item_at() method.
The highlighted_child property is the official API for accessing
the currently selected item. This fixes the AttributeError when
switching tabs, saving collections, or opening reader mode.

Closes #42
```

---

## Pull Request Process

### Before Opening a PR

- [ ] Branch is up to date with `upstream/main`.
- [ ] All tests pass: `pytest -xvs`.
- [ ] No new dependencies without justification in PR description.
- [ ] Constitution compliance verified (see checklist below).
- [ ] Commit messages follow Conventional Commits.
- [ ] Code is formatted with `black` (if applicable).
- [ ] CHANGELOG.md updated (for user-facing changes).

### Opening a PR

1. Push your branch to your fork.
2. Open a PR against `anubhavaanand/recon:main`.
3. Use the PR template if available. If not, include:

```markdown
## Description
What does this PR do? Why?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Constitution Compliance
- [ ] Zero-AI default maintained
- [ ] No new dependencies (or justified below)
- [ ] Keyboard-first (new feature has hotkey)
- [ ] Dry error voice (ERR: prefix)
- [ ] No modal dialogs
- [ ] Tests added/updated

## Testing
How was this tested? Include commands.

## Screenshots / Terminal Output
If applicable, paste TUI screenshots or terminal output.

## Checklist
- [ ] Tests pass
- [ ] No linting errors
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if user-facing)
```

### Review Process

| Stage | Who | What | Timeline |
|-------|-----|------|----------|
| **Automated** | GitHub Actions | CI runs tests, lint, security scan | Immediate |
| **Maintainer Review** | @anubhavaanand | Code review, constitution check | 48-72 hours |
| **Contributor Response** | You | Address feedback, push fixes | Variable |
| **Final Approval** | @anubhavaanand | Merge to `main` | After approval |

### What Reviewers Expect

- **Clear diff.** Each commit should be a logical step. Squash fixup commits before final review.
- **Test coverage.** New features need tests. Bug fixes need regression tests.
- **No surprises.** If the PR changes behavior, document it. If it adds a dependency, justify it.
- **Respect for history.** Do not rewrite history after the PR has been reviewed. Push new commits for fixes.

### After Merge

- Your branch will be deleted.
- Your contribution will be in the next release.
- You will be credited in CHANGELOG.md and release notes.

---

## Code Style & Linting

### Python Style

- **PEP 8** with these exceptions:
  - Line length: **100 characters** (not 79).
  - Type hints: **Required** for all function signatures.
  - Docstrings: **Google style** for modules, classes, and public functions.

### Formatting

```bash
# Format with black (line length 100)
black . --line-length 100

# Check formatting without modifying
black . --line-length 100 --check

# Sort imports
isort . --profile black

# Type checking (optional but recommended)
mypy recon/ --ignore-missing-imports
```

### Linting

```bash
# Run flake8
flake8 recon/ tests/ --max-line-length=100 --extend-ignore=E203,W503

# Run pylint (stricter)
pylint recon/ tests/ --max-line-length=100 --disable=C0111,R0903
```

### Configuration Files

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

### TUI-Specific Conventions

- Widget IDs use `snake_case`: `#info_tab`, `#result_list`.
- CSS classes use `kebab-case`: `.highlighted`, `.hidden`.
- Event handlers use `on_<widget>_<event>`: `on_tabbed_content_tab_activated`.
- Action methods use `action_<name>`: `action_save_collection`.
- All screens must have `BINDINGS` class variable documented.

---

## Testing Requirements

### Before Every PR

```bash
# Run the full test suite
pytest -xvs

# Expected output: all tests pass, no failures
# ===================================== 37 passed in 1.90s =====================================
```

### Test Coverage Expectations

| Change Type | Minimum Coverage | Notes |
|-------------|------------------|-------|
| Bug fix | Regression test required | Must fail before fix, pass after |
| New feature | Unit tests for all public methods | Mock external APIs |
| Refactor | Existing tests must still pass | No coverage regression |
| Documentation | No tests required | But verify examples work |
| Performance | Benchmark test if applicable | See `tests/test_performance.py` |

### Writing Tests

```python
# tests/test_example.py
import pytest
from core.models import PatentRecord

class TestPatentRecord:
    def test_from_dict_valid(self):
        data = {
            "id": "US12345678",
            "title": "Example Patent",
            "abstract": "An example.",
        }
        record = PatentRecord.from_dict(data)
        assert record.id == "US12345678"
        assert record.title == "Example Patent"

    def test_from_dict_missing_title(self):
        data = {"id": "US12345678"}
        record = PatentRecord.from_dict(data)
        assert record.title == "UNKNOWN"  # Missing data flagger
```

### Mocking External APIs

```python
# tests/test_patent_apis.py
import httpx
import pytest
from clients.patent_apis import USPTOClient

@pytest.mark.asyncio
async def test_uspto_search_mocked(monkeypatch):
    async def mock_get(*args, **kwargs):
        return httpx.Response(200, json={
            "response": {"docs": [{"patentNumber": "US123", "inventionTitle": "Mock"}]}
        })

    client = USPTOClient(api_key="test")
    monkeypatch.setattr(client, "get_with_backoff", mock_get)

    results = await client.search("test")
    assert len(results) == 1
    assert results[0].id == "US123"
```

### Test Categories

| Category | File Pattern | Run Command |
|----------|-------------|-------------|
| Unit | `test_*.py` | `pytest tests/test_models.py -xvs` |
| Integration | `test_integration_*.py` | `pytest tests/test_integration_new.py -xvs` |
| Performance | `test_performance.py` | `pytest tests/test_performance.py -v` |
| Security | `test_error_handling.py` | `pytest tests/test_error_handling.py -v` |
| Cache | `test_cache*.py` | `pytest tests/test_cache.py tests/test_cache_validation.py -v` |

---

## Definition of Done

A contribution is **done** when all of the following are true:

### For Code Changes

- [ ] Code compiles and runs without errors.
- [ ] All tests pass: `pytest -xvs` returns 0 failures.
- [ ] New code has tests with >= 80% line coverage.
- [ ] No new linting errors: `flake8` and `black --check` pass.
- [ ] Constitution compliance verified (see checklist in PR template).
- [ ] Error messages use `ERR:` prefix and are actionable.
- [ ] No `print()` statements without `INFO:` or `ERR:` prefix.
- [ ] No `except Exception: pass` patterns.
- [ ] Keyboard shortcuts documented in help overlay (if TUI feature).
- [ ] CHANGELOG.md updated with user-facing description.
- [ ] PR description is complete and follows template.
- [ ] Review feedback addressed and approved by maintainer.

### For Documentation Changes

- [ ] Spelling and grammar checked.
- [ ] All links verified (no 404s).
- [ ] Code examples tested and working.
- [ ] Screenshots / terminal output current with latest version.
- [ ] PR description explains what changed and why.

### For Dependency Changes

- [ ] Justification provided in PR description.
- [ ] License compatibility verified (MIT/Apache/BSD preferred).
- [ ] No transitive dependency conflicts.
- [ ] `pyproject.toml` and `requirements.txt` updated.
- [ ] CI passes with new dependency.

---

## Questions?

- **Open an issue** for bugs, feature requests, or general questions.
- **Start a discussion** (if enabled) for architecture or philosophy questions.
- **Email the maintainer** for sensitive security issues (see [Security Policy](SECURITY.md)).

If you are new to open source, welcome. If you are unsure about anything, ask. The maintainer would rather answer a question than reject a well-intentioned PR.

---

<p align="center">
  Thank you for contributing to RECON.<br>
  Terminal-native patent research, built with patience.
</p>
