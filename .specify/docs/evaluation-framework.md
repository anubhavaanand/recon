# Evaluation Framework Specification: RECON Testing & Quality Assurance

**Document ID**: `evaluation-framework`  
**Version**: 1.0.0  
**Created**: 2026-05-13  
**Status**: Active  
**Maintainer**: Development Team

---

## Overview

The RECON Evaluation Framework provides comprehensive testing, validation, and quality assurance across all components of the patent research TUI. It ensures compliance with the RECON Constitution and confirms functional requirements are met.

## Evaluation Scope

### 1. Core Module Testing (Unit Level)
**Modules**: `core/search.py`, `core/scoring.py`, `core/models.py`, `core/config.py`

**Test Coverage**:
- [ ] Search query validation and parameter handling
- [ ] Scoring algorithm correctness (equal weighting validation)
- [ ] Data model serialization/deserialization
- [ ] Cache hit/miss behavior
- [ ] Rate limiting backoff sequences
- [ ] Error handling for API failures

**Success Criteria**:
- Minimum 85% code coverage
- All edge cases from spec.md tested
- Rate limiting backoff works: 1s → 2s → 4s → 8s → graceful fail
- Missing data flagged (not omitted)

---

### 2. Client API Testing (Integration Level)
**Modules**: `clients/patent_apis.py`, `clients/intelligence.py`, `clients/base.py`

**Test Coverage**:
- [ ] USPTO API connectivity and response parsing
- [ ] EPO, WIPO, Google Patents, Lens API handling
- [ ] Cross-reference intelligence API calls (NIH, NSF, SEC, OpenAlex, arXiv, OpenCorporates)
- [ ] 429 (Rate Limit) response handling
- [ ] Timeout and connection error recovery
- [ ] Response validation against expected schema

**Success Criteria**:
- All API clients handle 429 with backoff
- Malformed responses logged with actionable errors
- Timeouts don't cascade (fail fast, circuit break)
- Equal weighting confirmed for all scoring signals

---

### 3. TUI Component Testing (Widget Level)
**Modules**: `tui/widgets/result_list.py`, `tui/widgets/info_tab.py`, `tui/widgets/claims_tab.py`, `tui/widgets/image_tab.py`

**Test Coverage**:
- [ ] Widget initialization and state management
- [ ] Result list rendering (descending sort verification)
- [ ] Tab switching (Info → Claims → Image)
- [ ] Navigation highlighting and selection logic
- [ ] Keyboard input handling (arrow keys, Enter, etc.)
- [ ] Missing data display (e.g., `[?] UNKNOWN`)

**Success Criteria**:
- Keyboard navigation updates preview in <100ms
- Tab content updates on selection
- No entries silently removed from list
- Invalid data marked as `[?]` or `UNKNOWN`

---

### 4. TUI Integration Testing (Screen Level)
**Modules**: `tui/screens.py`, `tui/app.py`

**Test Coverage**:
- [ ] Application startup and initialization
- [ ] Tab lifecycle (loading, binding, updating)
- [ ] Search query execution and result display
- [ ] Preview panel synchronization with selection
- [ ] Image rendering (terminal protocol detection)
- [ ] Navigation state persistence
- [ ] Error message display and actionability

**Success Criteria**:
- Initial search results load in <3 seconds
- Preview updates <100ms after selection
- Terminal protocol fallback works (Kitty → iTerm2 → Sixel → External)
- All errors provide actionable resolution steps

---

### 5. Export & Collection Testing
**Modules**: `cli/export.py`

**Test Coverage**:
- [ ] Collection save/load functionality
- [ ] PDF export generation
- [ ] Markdown export formatting
- [ ] JSON export structure
- [ ] BibTeX export correctness
- [ ] CSV export parsing
- [ ] Reader mode toggle and rendering

**Success Criteria**:
- Exported files match expected format
- 100% of collection items present in export
- Reader mode hides UI chrome appropriately
- No data loss during export

---

### 6. Import & Dependency Validation
**Coverage**: All Python modules

**Test Coverage**:
- [ ] No circular dependencies detected
- [ ] All imports resolvable
- [ ] External dependencies (textual, httpx, etc.) available
- [ ] Version compatibility verified
- [ ] Missing optional dependencies handled gracefully

**Success Criteria**:
- `python -c "import recon"` succeeds
- All modules importable from project root
- No `ImportError` on startup
- Graceful fallback for optional features

---

### 7. Cache & Storage Testing
**Modules**: `storage/`, cache behavior in `core/`

**Test Coverage**:
- [ ] SQLite cache creation and schema
- [ ] Cache write/read performance
- [ ] TTL enforcement (30-day refresh for metadata)
- [ ] Append-only citations behavior
- [ ] Cache eviction on disk full
- [ ] Corruption recovery

**Success Criteria**:
- Cache indefinite for document content
- Metadata refreshed every 30 days
- Citations append-only (never overwritten)
- Corrupted cache recoverable without data loss

---

### 8. Performance Benchmarking
**Metrics**: Latency, throughput, resource usage

**Test Coverage**:
- [ ] Search query → first result <3 seconds
- [ ] Keyboard navigation → preview update <100ms
- [ ] Tab switch latency
- [ ] Memory usage under load (1000+ results)
- [ ] CPU usage during search
- [ ] API request/response throughput

**Success Criteria**:
- SC-001: Initial search <3 seconds
- SC-002: Navigation preview <100ms
- Memory stable under 500MB for typical workload
- No memory leaks on extended navigation

---

### 9. Error Handling & Recovery Testing
**Focus**: Deterministic error voice

**Test Coverage**:
- [ ] All error messages tested for clarity
- [ ] Actionable resolution steps present
- [ ] No generic "An error occurred" messages
- [ ] Rate limit errors include API key guidance
- [ ] Unsupported image format handling
- [ ] Terminal capability detection errors

**Success Criteria**:
- 100% of errors provide exact reason
- 100% of errors include resolution steps
- Error voice matches constitution (dry, factual, terse)
- No apologies or conversational fluff

---

### 10. Data Integrity Testing
**Focus**: Constitution compliance

**Test Coverage**:
- [ ] No silent data omission
- [ ] Descending sort verification
- [ ] Equal weighting of scoring signals
- [ ] Missing data flags (never imputed)
- [ ] Deterministic results (no AI/ML sorting)
- [ ] Collection data integrity after export

**Success Criteria**:
- 100% of results present in sorted list
- No hidden AI/semantic reranking
- Missing values marked `[?]`, never guessed
- Reproducible results for identical queries

---

## Test Execution Strategy

### Baseline Assessment
1. Run all unit tests: `pytest tests/`
2. Run integration tests: `pytest tests/ -m integration`
3. Import validation: `python -c "import cli; import tui; import core; import clients; import storage"`
4. Generate coverage report: `pytest --cov=cli,tui,core,clients,storage --cov-report=html`

### Continuous Evaluation
- **Pre-commit**: Import validation + critical tests
- **On PR**: Full test suite + coverage enforcement
- **Nightly**: Performance benchmarks + cache validation
- **Weekly**: Manual UX testing + constitution compliance audit

### Health Check (Quick Validation)
```bash
python tests/health_check.py --format=json
```
Returns:
- Import status
- Test count passing/failing
- Coverage percentage
- Critical issues (blockers)
- Warnings (non-critical)

---

## Reporting & Metrics

### Evaluation Report
- **Generated by**: `tests/evaluation_report.py`
- **Frequency**: After each test run
- **Contents**:
  - Test summary (pass/fail/skip)
  - Coverage metrics per module
  - Performance benchmarks
  - Critical issues identified
  - Constitution compliance audit
  - Recommendations for fixes

### Key Metrics Dashboard
1. **Code Quality**: Coverage %, test pass rate
2. **Performance**: Search latency p50/p95, navigation latency, memory peak
3. **Reliability**: Error recovery rate, data integrity checks passed
4. **Compliance**: Constitution principle adherence, specification conformance

---

## Constitution Alignment Matrix

| Principle | Validation Method | Test Module |
|-----------|------------------|------------|
| Zero-AI Default | Deterministic result verification | `test_determinism.py` |
| Transparency | Data output inspection | `test_data_integrity.py` |
| Equal Weights | Scoring algorithm audit | `test_scoring.py` |
| Descending Sort | Result ordering verification | `test_search.py` |
| Terminal-Native | No GUI detection/fallback | `test_tui_integration.py` |
| Speed over Depth | Latency benchmarks <3s, <100ms | `test_performance.py` |
| Uncertainty Flagged | Missing data explicitly marked | `test_models.py` |
| Actionable Errors | Error message quality audit | `test_error_handling.py` |

---

## Critical Success Factors

1. **Every module has tests**: No untested code in production
2. **Import validation on startup**: Catch dependency issues early
3. **Tab loading verified**: No preview blank-slate issues
4. **Cache validated**: TTL/append-only behavior confirmed
5. **Performance thresholds enforced**: <3s search, <100ms navigation
6. **Error messages audited**: 100% actionable, deterministic
7. **Constitution audit quarterly**: Drift detection
8. **Regression detection**: Baseline metrics tracked over time

---

## Test Data & Fixtures

- **Mock API responses**: `.specify/fixtures/api_responses/`
- **Test patents**: Pre-populated SQLite cache for deterministic testing
- **Terminal capabilities**: Mock Kitty/iTerm2/Sixel detection
- **Error scenarios**: Timeouts, 429s, malformed JSON, corrupted cache

---

## Maintenance & Evolution

- **Quarterly review**: Align framework with specification changes
- **Metric calibration**: Adjust thresholds based on real-world performance
- **Test debt**: Refactor flaky tests, improve isolation
- **Documentation**: Keep this specification up-to-date with implementation

---

## Related Documents

**For detailed task breakdown and implementation sequencing:**
- See `.specify/tasks/EVALUATION_TASKS.md` - Contains 8 task groups, 15 specific tasks, Phase 1-4 sequencing

**For constitution compliance details:**
- See `.specify/docs/constitution.md` - Core principles all tests must validate

**For product requirements and user stories:**
- See `.specify/docs/spec.md` - Functional requirements driving test coverage

---

## Success Definition

✅ **The RECON project is healthy when**:
1. All unit tests pass
2. Coverage ≥ 85% across core modules
3. Initial search <3 seconds
4. Navigation preview <100ms
5. No import errors on startup
6. Tab loading works (preview populated)
7. 100% of errors are actionable
8. Cache TTL/append-only verified
9. Constitution principles audited passing
10. No regression in performance baseline

