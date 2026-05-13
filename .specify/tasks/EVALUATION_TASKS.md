# Evaluation Framework Implementation Tasks

**Reference Document**: `.specify/docs/evaluation-framework.md`  
**Status**: Ready for Implementation  
**Priority**: P1 - Critical Infrastructure

---

## Task Group 1: Import & Dependency Validation

### Task 1.1: Create Import Validation Module
**File**: `tests/test_imports.py`  
**Objective**: Validate all modules are importable, detect circular dependencies

**Checklist**:
- [ ] Test `import recon` succeeds
- [ ] Test each module importable individually: cli, tui, core, clients, storage
- [ ] Detect circular dependencies using `importlib`
- [ ] Verify external dependencies (textual, httpx, Pillow, etc.) available
- [ ] Test graceful fallback for optional dependencies
- [ ] Document any soft dependencies

**Success Criteria**:
- All tests pass
- No ImportError on startup
- Circular dependency report generated
- CI integration ready

**Related Tests**: `tests/test_terminal_protocols.py` (existing)

---

### Task 1.2: Create Health Check Script
**File**: `tests/health_check.py`  
**Objective**: Standalone script for quick project status verification

**Checklist**:
- [ ] Import validation
- [ ] Test count summary (pass/fail/skip)
- [ ] Coverage percentage
- [ ] Critical issue detection
- [ ] JSON/human-readable output formats
- [ ] Exit codes: 0 (healthy), 1 (warnings), 2 (critical)

**Success Criteria**:
- Runs in <5 seconds
- Outputs actionable summary
- Can be called from CI/pre-commit hooks
- Runnable standalone: `python tests/health_check.py`

**Usage Examples**:
```bash
python tests/health_check.py                    # Human-readable
python tests/health_check.py --format=json      # JSON
python tests/health_check.py --format=critical  # Critical issues only
```

---

## Task Group 2: Widget & Component Testing

### Task 2.1: Create Widget Component Test Suite
**File**: `tests/test_tui_components.py`  
**Objective**: Test TUI widgets in isolation (result_list, info_tab, claims_tab, image_tab)

**Checklist**:
- [ ] Test ResultList widget rendering and state
- [ ] Test InfoTab content population
- [ ] Test ClaimsTab content population
- [ ] Test ImageTab protocol detection
- [ ] Test widget state synchronization
- [ ] Test keyboard event handling
- [ ] Mock Textual app context for widget testing

**Success Criteria**:
- All widgets render without errors
- State management verified
- Keyboard events trigger correct handlers
- Content displays correctly with test data

**Mock Data**:
- Sample patent records from `tests/fixtures/`
- Mock API responses for cross-references

**Related Tests**: `tests/test_tui_navigation.py` (existing)

---

### Task 2.2: Create Tab Integration Test Suite
**File**: `tests/test_tab_integration.py`  
**Objective**: Test tab lifecycle, loading, and preview synchronization

**Checklist**:
- [ ] Test tab initialization on app startup
- [ ] Test tab switching (Info → Claims → Image)
- [ ] Test tab content loading on selection
- [ ] Test preview panel population
- [ ] Test missing data handling (flagged as `[?]`)
- [ ] Test navigation state persistence
- [ ] Test keyboard navigation integration
- [ ] Verify <100ms preview update latency

**Success Criteria**:
- Tab switching works smoothly
- Preview updates on selection
- No blank/missing content
- Performance meets <100ms target
- All tab transitions tested

**Known Issues to Test**:
- Previously: tab content not loading → test this is fixed
- Verify `_load_active_tab()` works correctly
- Ensure tab IDs are properly prefixed

---

## Task Group 3: Core Module Testing

### Task 3.1: Enhance Scoring Tests
**File**: `tests/test_scoring.py`  
**Objective**: Verify equal weighting of scoring signals per Constitution

**Checklist**:
- [ ] Audit all scoring functions for equal weighting
- [ ] Test weight values across signals (NIH, NSF, SEC, etc.)
- [ ] Verify no hidden/variable weighting
- [ ] Test scoring determinism (same input → same output)
- [ ] Document all weights and their origins

**Success Criteria**:
- All signals weighted equally (or document exception with justification)
- Scoring is deterministic
- Constitution principle verified: ✅ Equal Weights

---

### Task 3.2: Enhance Search Tests
**File**: `tests/test_search.py`  
**Objective**: Verify search results are complete, descending sorted, no entries dropped

**Checklist**:
- [ ] Test complete result set returned (no silent omission)
- [ ] Test descending sort order
- [ ] Test sort stability across API sources
- [ ] Test missing data flags (never imputed)
- [ ] Test query validation and error handling
- [ ] Test rate limit handling and backoff
- [ ] Verify <3 second initial search time

**Success Criteria**:
- 100% of results present in sorted list
- No entries silently removed
- Descending sort verified
- Missing data marked `[?]`, not guessed
- Constitution principles verified: ✅ Descending Sort, Uncertainty Flagged

---

### Task 3.3: Create Cache Validation Tests
**File**: `tests/test_cache_validation.py`  
**Objective**: Verify cache TTL, append-only, and corruption recovery

**Checklist**:
- [ ] Test indefinite cache for document content
- [ ] Test 30-day refresh for metadata
- [ ] Test append-only behavior for citations
- [ ] Test cache creation and schema validation
- [ ] Test corrupted cache recovery
- [ ] Test cache eviction policies
- [ ] Test concurrent access (thread-safe)

**Success Criteria**:
- Cache behavior matches specification exactly
- No data loss during corruption recovery
- TTL enforcement verified
- Thread-safety confirmed

---

## Task Group 4: Performance Benchmarking

### Task 4.1: Create Performance Benchmark Suite
**File**: `tests/test_performance.py`  
**Objective**: Measure and verify performance thresholds

**Benchmarks**:
- [ ] Search query → first result latency (target: <3s)
- [ ] Keyboard navigation → preview update (target: <100ms)
- [ ] Tab switch latency
- [ ] Memory usage under load (1000+ results)
- [ ] CPU usage during search
- [ ] Cache hit performance

**Success Criteria**:
- SC-001: Search <3 seconds ✅
- SC-002: Navigation <100ms ✅
- Memory baseline established
- Results tracked over time for regression detection

**Output**:
- JSON report with timestamps
- Historical comparison capability
- Regression alerts if thresholds exceeded

---

## Task Group 5: Error Handling & Voice

### Task 5.1: Create Error Message Audit
**File**: `tests/test_error_handling.py`  
**Objective**: Audit all error messages for clarity, actionability, and voice consistency

**Checklist**:
- [ ] No "An error occurred" generic messages
- [ ] Every error includes exact reason
- [ ] Every error includes resolution steps
- [ ] Error voice is dry, factual, terse (no apologies)
- [ ] Rate limit errors include API key guidance
- [ ] Image format errors include fallback info
- [ ] Terminal capability errors include config steps

**Error Scenarios to Test**:
- Network timeout
- API rate limit (429)
- Malformed API response
- Missing patent image
- Unsupported terminal protocol
- Corrupted cache
- Invalid search query
- Missing API credentials

**Success Criteria**:
- 100% of errors provide reason + resolution
- Constitution principle verified: ✅ Dry, Actionable Error Voice
- Error voice audit passed

---

## Task Group 6: Reporting & Automation

### Task 6.1: Create Evaluation Report Generator
**File**: `tests/evaluation_report.py`  
**Objective**: Generate comprehensive evaluation report after test runs

**Report Contents**:
- [ ] Test summary (count: pass/fail/skip)
- [ ] Coverage metrics per module (target: 85%+)
- [ ] Performance benchmarks (search, navigation, memory)
- [ ] Critical issues identified (blocker list)
- [ ] Warnings (non-blocking)
- [ ] Constitution compliance audit matrix
- [ ] Recommendations for fixes

**Output Formats**:
- [ ] Human-readable markdown
- [ ] JSON for CI integration
- [ ] HTML dashboard (optional)

**Success Criteria**:
- Report generated after each test run
- Clearly identifies blockers vs. warnings
- Tracks metrics over time
- CI-friendly JSON format

**Usage**:
```bash
python tests/evaluation_report.py --format=markdown > EVALUATION.md
python tests/evaluation_report.py --format=json > evaluation.json
```

---

### Task 6.2: Create CI/Pre-Commit Integration
**File**: `.specify/scripts/bash/validate-evaluation.sh`  
**Objective**: Integrate evaluation framework into CI/pre-commit workflows

**Checklist**:
- [ ] Pre-commit hook runs critical tests + import validation
- [ ] CI runs full test suite + coverage enforcement
- [ ] Nightly performance benchmarks
- [ ] Weekly constitution audit
- [ ] Report generation and archival

**Integration Points**:
- [ ] Pre-commit: `health_check.py` + critical tests
- [ ] CI: Full test suite + coverage report
- [ ] GitHub Actions: Nightly benchmarks
- [ ] Manual: Constitution audit (quarterly)

---

## Task Group 7: Documentation & Knowledge Base

### Task 7.1: Create EVALUATION.md Runbook
**File**: `EVALUATION.md` (root)  
**Objective**: User-friendly guide to running evaluation framework

**Contents**:
- [ ] Quick start: `python tests/health_check.py`
- [ ] Full evaluation: `pytest tests/ && python tests/evaluation_report.py`
- [ ] Performance benchmarks: `pytest tests/test_performance.py`
- [ ] Coverage report: `pytest --cov=...`
- [ ] Troubleshooting common issues
- [ ] Interpreting evaluation reports
- [ ] Constitution compliance checklist

**Success Criteria**:
- Non-technical users can run evaluation
- Clear instructions for each scenario
- Actionable troubleshooting steps

---

### Task 7.2: Create Test Fixture Documentation
**File**: `tests/fixtures/README.md`  
**Objective**: Document all test data and mock responses

**Contents**:
- [ ] Sample patent records schema
- [ ] Mock API responses (USPTO, EPO, etc.)
- [ ] Terminal capability mocks (Kitty, iTerm2, Sixel)
- [ ] Error scenario responses
- [ ] How to add new fixtures
- [ ] Data generation scripts

---

## Task Group 8: Critical Path Verification

### Task 8.1: Verify Tab Loading Fix
**File**: `tests/test_tab_integration.py::test_tab_content_loads_on_selection`  
**Objective**: Confirm previously identified tab loading issue is resolved

**Context**: 
- Issue: Preview tab was not populating with content after selection
- Fix: Updated `_load_active_tab()` to use `.update()` method
- Verification: Tab content loads correctly and displays in preview

**Checklist**:
- [ ] Tab content populated on selection
- [ ] Preview panel displays content
- [ ] No blank/missing content in preview
- [ ] Multiple tab switches work smoothly

**Success Criteria**:
- Tab loading works as expected
- No regression from previous fixes

---

### Task 8.2: Verify Import Error Resolved
**File**: `tests/test_imports.py::test_search_patents_import`  
**Objective**: Confirm previously identified import error is resolved

**Context**:
- Issue: ImportError for `search_patents` function
- Fix: Corrected imports in relevant modules
- Verification: All imports resolve on startup

**Checklist**:
- [ ] `search_patents` function importable
- [ ] All dependent modules resolve
- [ ] No circular dependency issues
- [ ] `import recon` succeeds

**Success Criteria**:
- No ImportError on startup
- All critical imports verified

---

## Implementation Priority & Sequencing

### Phase 1: Foundation (Week 1)
1. Task 1.1: Import Validation Module
2. Task 1.2: Health Check Script
3. Task 8.1: Verify Tab Loading Fix
4. Task 8.2: Verify Import Error Resolved

### Phase 2: Component Testing (Week 2)
5. Task 2.1: Widget Component Tests
6. Task 2.2: Tab Integration Tests
7. Task 3.1: Enhance Scoring Tests
8. Task 3.2: Enhance Search Tests

### Phase 3: Advanced (Week 3)
9. Task 3.3: Cache Validation Tests
10. Task 4.1: Performance Benchmarks
11. Task 5.1: Error Message Audit

### Phase 4: Automation & Reporting (Week 4)
12. Task 6.1: Evaluation Report Generator
13. Task 6.2: CI Integration
14. Task 7.1: EVALUATION.md Runbook
15. Task 7.2: Test Fixture Documentation

---

## Cross-Module Dependencies

```
test_imports.py (Task 1.1)
  └─ Blocks: All other tests (foundation)
  
health_check.py (Task 1.2)
  └─ Depends: test_imports, all test suites
  
test_tui_components.py (Task 2.1)
  └─ Depends: health_check, test_imports
  └─ Used by: test_tab_integration.py

test_tab_integration.py (Task 2.2)
  └─ Depends: test_tui_components, health_check
  └─ Critical: Validates tab loading fix

test_performance.py (Task 4.1)
  └─ Depends: All core tests passing
  └─ Produces: Baseline metrics

evaluation_report.py (Task 6.1)
  └─ Depends: All test modules
  └─ Produces: Comprehensive report
```

---

## Definition of Done

✅ **Evaluation Framework is complete when**:
1. All tasks in all groups completed
2. All success criteria met
3. Health check script operational
4. Evaluation report generated
5. CI integration active
6. Documentation complete and accurate
7. Baseline metrics captured
8. Constitution audit passed
9. No critical issues outstanding
10. Team trained on running evaluation

---

## Related Specifications
- `.specify/docs/spec.md` - Feature requirements
- `.specify/docs/constitution.md` - Core principles
- `.specify/docs/evaluation-framework.md` - Detailed framework specification

