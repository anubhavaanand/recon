# RECON Production-Ready Plan

**Branch**: `production-ready-v1.0.0` (new from `main`)  
**Goal**: Stabilize, verify, and ship RECON to production quality  
**Constraint**: Constitution-locked stack (Python 3.12+, Textual, httpx, Pillow, rapidfuzz, typer, SQLite)

---

## Current State Assessment

| Aspect | Status | Risk |
|--------|--------|------|
| Codebase | 41 milestones claimed complete | High — git shows deleted test files, untracked duplicates |
| Tests | Claims 37/37 passing | Unverified — PRD Q006 unresolved |
| Stack | Constitution-locked | Low — framework already chosen |
| Packaging | v0.2.0 in pyproject.toml | Medium — no PyPI release yet |
| CI/CD | None | High — no automated validation |
| Docs | README exists, CONTRIBUTING/SECURITY missing | Medium |

---

## Phase 1: Stabilize (0-15 min)

### 1.1 Create Production Branch
```bash
git checkout -b production-ready-v1.0.0 main
```

### 1.2 Restore Git State
- Restore deleted test files from `tests/` (currently untracked duplicates exist)
- Commit clean state before making changes

### 1.3 Run Health Check
- Execute `python tests/health_check.py --format=json`
- Execute `python tests/evaluation_report.py --format=json`
- Baseline: import status, dependency check, test pass/fail, coverage %

---

## Phase 2: Verify & Fix Critical Issues (15-45 min)

### 2.1 Fix Test Suite
- Run `pytest tests/ -x` to identify failures
- Fix any import errors, missing fixtures, or broken test files
- Target: 100% test pass rate

### 2.2 Resolve PRD Open Questions
| Question | Action |
|----------|--------|
| Q001: TUI preview tab populates? | Manual TUI test + automated widget test |
| Q002: Live APIs tested? | Run `recon config test` with mocked keys |
| Q003: EPO OAuth implemented? | Verify `clients/patent_apis.py` |
| Q004: Phase C tests exist? | Create if missing |
| Q005: Constitution audit verified? | Run grep checks for `ERR:`, `openai`, `except: pass` |

### 2.3 Code Quality Pass
- Run `ruff check .` — fix linting errors
- Run `mypy .` — fix type errors
- Ensure `python -c "import cli; import tui; import core; import clients; import storage"` succeeds

---

## Phase 3: Production Hardening (45-75 min)

### 3.1 Packaging
- Verify `pyproject.toml` has complete metadata
- Test `python -m build` produces valid wheel + sdist
- Test `pip install dist/*.whl` works and `recon --help` succeeds

### 3.2 CI/CD
- Create `.github/workflows/ci.yml`
- Matrix: Python 3.12, 3.13
- Steps: lint (ruff), typecheck (mypy), test (pytest), security (pip-audit)

### 3.3 Documentation
- Verify README.md badges, install instructions, keyboard shortcuts
- Create SECURITY.md (vulnerability reporting)
- Verify CONTRIBUTING.md exists

### 3.4 Performance Benchmarks
- Run `pytest tests/test_performance.py`
- Verify: search <3s (cached), navigation <100ms
- Memory <100MB for 1000 patents

---

## Phase 4: Final Evaluation (75-60 min)

### 4.1 Full Test Suite
```bash
pytest tests/ --cov=cli,tui,core,clients,storage --cov-report=term
```
- Target: ≥85% coverage, 0 failures

### 4.2 Constitution Audit
- Verify no `openai`/`anthropic`/`ollama` imports in default path
- Verify all errors start with `ERR:`
- Verify no `except: pass` blocks
- Verify equal-weight scoring in `core/scoring.py`

### 4.3 Packaging Test
```bash
python -m build
pip install dist/recon_patent-*.whl
recon --help
recon search "test" --format json
```

---

## Rollout

1. Commit all changes to `production-ready-v1.0.0`
2. Push branch
3. Open PR with evaluation report
4. Merge to main after green CI
5. Tag `v1.0.0` and publish to PyPI

---

## Risks

| Risk | Mitigation |
|------|------------|
| Tests fail due to environment | Fix environment, mock network calls |
| TUI crashes on tab switch | Fix `highlighted_child` access pattern |
| APIs blocked in sandbox | Use mocked responses for CI |
| Constitution violation found | Remove/replace offending code |

---

## Success Criteria

- [ ] All tests pass (`pytest tests/` = 0 failures)
- [ ] Coverage ≥85%
- [ ] `python -m build` succeeds
- [ ] `pip install .` + `recon --help` works
- [ ] No `ERR:` violations in codebase
- [ ] No hidden AI imports
- [ ] CI/CD pipeline green
- [ ] README + SECURITY.md present
