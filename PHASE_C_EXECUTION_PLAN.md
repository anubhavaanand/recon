# Phase C Execution Plan: Advanced Testing

**Phase**: Evaluation Phase C (Advanced Testing)  
**Parallel to**: Development Phases 4-5  
**Priority**: P1 - Critical Infrastructure  
**Status**: Ready for Implementation  

---

## Overview

Phase C focuses on advanced testing across three critical areas:
1. **Cache system validation** - Storage layer integrity (Task 3.3)
2. **Performance benchmarking** - Latency and throughput verification (Task 4.1)
3. **Error handling audit** - Message quality and actionability (Task 5.1)

These tasks validate core constitutional principles and ensure production readiness.

---

## Task 3.3: Cache Validation Tests

**File**: `tests/test_cache_validation.py`  
**Priority**: P1 - Critical Infrastructure  
**Estimated Effort**: 8-10 hours  

### Goal
Verify that the caching system maintains data integrity, enforces TTL policies, and recovers gracefully from corruption. This validates the storage layer's compliance with RECON specifications:
- Document content cached indefinitely
- Metadata refreshed every 30 days
- Citations are append-only (never overwritten)
- Corrupted caches recoverable without data loss

### Test Cases

#### 1. `test_cache_indefinite_for_documents()`
**Assertions**:
- Create cache entry for patent document at T=0
- Verify entry exists at T=30 days (no TTL expiration)
- Verify entry exists at T=365 days (no expiration)
- Assert cache entry is identical to original (no mutations)
- Verify `cache.hit()` returns True for document queries at all time points

**Test Data**:
```python
document_record = {
    "patent_id": "US10123456B2",
    "title": "Artificial Intelligence System",
    "abstract": "A system for AI-driven patent analysis",
    "claims": "1. A method comprising...",
    "images": ["image_url_1", "image_url_2"]
}
```

**Success Criteria**:
- Document entries have no TTL in database schema
- SELECT query confirms NULL ttl_seconds for document type
- Cache hit logic never evicts document entries

#### 2. `test_metadata_refresh_30_days()`
**Assertions**:
- Create cache entry for patent metadata at T=0 with `refresh_needed=False`
- Verify cache hit at T=29 days (within TTL)
- Verify cache hit becomes `False` at T=30 days + 1 minute
- Assert metadata is accessible for re-fetch at T=30 days
- Verify subsequent fetch updates `last_refreshed` timestamp

**Test Data**:
```python
metadata_record = {
    "patent_id": "US10123456B2",
    "citations_count": 47,
    "forward_citations": 12,
    "npl_count": 8,
    "classification": "G06F-17/30"
}
```

**Success Criteria**:
- Metadata TTL = 30 days exactly
- `cache.hit()` returns False after 30 days
- Refresh timestamp updated on subsequent fetch
- No partial data returned during refresh window

#### 3. `test_citations_append_only()`
**Assertions**:
- Create patent with initial citations list: `["US1111111", "US2222222"]`
- Add new citation: `["US1111111", "US2222222", "US3333333"]`
- Verify all 3 citations present in cache
- Attempt to remove citation (should fail or no-op)
- Verify original citations never removed
- Assert citation order preserved
- Verify no duplicate citations added

**Test Data**:
```python
patent_with_citations = {
    "patent_id": "US10123456B2",
    "citations": ["US1111111", "US2222222"]
}
# After refresh:
patent_with_citations["citations"] = ["US1111111", "US2222222", "US3333333"]
```

**Success Criteria**:
- Append operation confirmed in database audit log
- Citation count only increases (never decreases)
- No UPDATE operations on citations field (only INSERT/APPEND)
- Duplicate check prevents re-adding same citation

#### 4. `test_corrupted_cache_recovery()`
**Assertions**:
- Create valid cache database with 5 patent records
- Corrupt database: truncate random row, insert malformed JSON
- Attempt cache read: should not crash
- Assert recovery mechanism detects corruption
- Verify backup is available or entries are skipped
- Assert remaining valid entries are accessible
- Verify cache rebuilds cleanly after corruption

**Test Data**:
```python
# Corruption scenarios:
# 1. Truncate row: DELETE FROM cache WHERE id=3;
# 2. Malformed JSON: UPDATE cache SET data='{"invalid json...' WHERE id=2;
# 3. Missing table: DROP TABLE cache;
# 4. Checksum mismatch: Alter stored hash value
```

**Success Criteria**:
- Corruption detected (not silently ignored)
- Cache.open() doesn't raise unrecoverable error
- Recovery path documented in logs
- At least N-1 records recoverable (where N = pre-corruption count)
- Backup snapshot restored (if available)

#### 5. `test_cache_schema_validation()`
**Assertions**:
- Verify SQLite schema on cache initialization
- Assert required columns present: `patent_id, data, type, ttl_seconds, last_refreshed, created_at`
- Verify indexes on `patent_id` and `type`
- Assert data column type is BLOB or TEXT
- Verify timestamps are INTEGER (Unix epoch)

**Success Criteria**:
- Schema matches specification exactly
- All constraints enforced (PRIMARY KEY, NOT NULL)
- Indexes present for query performance
- Version tracking available

#### 6. `test_cache_concurrent_access()`
**Assertions**:
- Spawn 10 concurrent threads accessing cache
- Thread 1-5: Read patent data
- Thread 6-8: Append citations
- Thread 9-10: Refresh metadata
- Assert no race conditions or data corruption
- Verify all operations completed successfully
- Assert no locks cause timeouts (>1 second)

**Success Criteria**:
- Thread-safe operations confirmed
- No deadlocks detected
- All threads complete within 5 seconds
- Data integrity verified post-concurrency

### Success Criteria (from specification)
- ✅ Cache behavior matches specification exactly
- ✅ No data loss during corruption recovery
- ✅ TTL enforcement verified for metadata (30 days)
- ✅ Append-only behavior verified for citations
- ✅ Thread-safety confirmed
- ✅ Document indefinite caching verified
- ✅ Schema validation complete

### Dependencies
- `storage/` module fully implemented
- SQLite driver available
- No external API calls required (use fixtures)

### Commit Message
```
feat: add cache validation test suite (Task 3.3)

Verify cache system maintains data integrity and enforces policies:
- Document content cached indefinitely
- Metadata refreshed every 30 days
- Citations append-only (never overwritten)
- Corrupted caches recoverable without data loss
- Thread-safe concurrent access verified

Tests: 6 test cases, 100% cache module coverage
Success Criteria: All 7 requirements met
```

---

## Task 4.1: Performance Benchmark Suite

**File**: `tests/test_performance.py`  
**Priority**: P1 - Constitutional (Speed over Depth)  
**Estimated Effort**: 10-12 hours  

### Goal
Establish performance baselines and verify that the application meets critical latency requirements:
- Search query → first result: **<3 seconds** (SC-001)
- Keyboard navigation → preview update: **<100ms** (SC-002)
- Memory stable under 500MB for typical workload
- No memory leaks on extended navigation

### Test Cases

#### 1. `test_search_latency_first_result()`
**Assertions**:
- Execute search query with mock API responses
- Measure time from `search_patents()` call to first result available
- Assert latency < 3000ms
- Record p50, p95, p99 latencies
- Test with different query complexities: simple, boolean, phrase

**Test Data**:
```python
queries = [
    ("AI patent", "simple search"),
    ("artificial intelligence AND machine learning", "boolean search"),
    ('"neural network" classification:G06F', "phrase + filter")
]
```

**Success Criteria**:
- ✅ SC-001: All queries return first result in <3 seconds
- ✅ p95 latency < 2.8 seconds
- ✅ No variance > 500ms between runs (deterministic)
- ✅ Baseline captured for regression detection

#### 2. `test_navigation_preview_latency()`
**Assertions**:
- Render result list with 100 patents
- Select first result (simulate keyboard press)
- Measure time from selection to preview panel update
- Assert latency < 100ms
- Repeat for 10 consecutive selections
- Assert no latency degradation

**Test Data**:
```python
test_patents = [
    {"patent_id": f"US{1000000+i}B2", "title": f"Patent {i}"} 
    for i in range(100)
]
```

**Success Criteria**:
- ✅ SC-002: All navigation updates < 100ms
- ✅ Average latency < 50ms
- ✅ No latency increase after 100 selections
- ✅ p99 latency < 120ms

#### 3. `test_tab_switch_latency()`
**Assertions**:
- Load patent with content in Info tab
- Switch to Claims tab (measure load time)
- Switch to Image tab (measure load time)
- Assert each tab switch < 200ms
- Test with large content (1000+ characters)

**Success Criteria**:
- Info → Claims switch < 200ms
- Claims → Image switch < 200ms
- Large content doesn't impact latency
- No UI blocking during load

#### 4. `test_memory_under_load()`
**Assertions**:
- Load cache with 1000 patent records
- Measure baseline memory usage
- Render result list with all 1000 patents
- Navigate through 50 sequential selections
- Measure peak memory usage
- Assert peak < 500MB
- Check for memory leaks (final usage < baseline + 50MB)

**Test Data**:
```python
large_dataset = [
    generate_test_patent() for _ in range(1000)
]
```

**Success Criteria**:
- ✅ Baseline memory < 100MB
- ✅ Peak under load < 500MB
- ✅ Memory after 50 navigations < baseline + 50MB
- ✅ No unbounded growth detected

#### 5. `test_cpu_during_search()`
**Assertions**:
- Monitor CPU usage during search operation
- Assert CPU < 80% utilization
- Verify search doesn't block other threads
- Test during concurrent cache access

**Success Criteria**:
- Search doesn't monopolize CPU
- Other threads remain responsive
- CPU usage drops after search completes

#### 6. `test_cache_hit_performance()`
**Assertions**:
- Execute search query (cold cache)
- Measure latency (T1)
- Execute identical query (warm cache)
- Measure latency (T2)
- Assert T2 < T1 * 0.5 (50% improvement)
- Assert cache hit latency < 50ms

**Success Criteria**:
- Cache hits significantly faster than misses
- Cache hit latency < 50ms
- Consistent performance across repeated hits

### Performance Report Output
Each test generates a JSON report:
```json
{
  "timestamp": "2026-05-13T10:30:00Z",
  "test_name": "test_search_latency_first_result",
  "metrics": {
    "p50_ms": 1250,
    "p95_ms": 2400,
    "p99_ms": 2800,
    "min_ms": 1100,
    "max_ms": 2900,
    "avg_ms": 1400,
    "threshold_ms": 3000,
    "passed": true,
    "regression": false
  },
  "baseline_comparison": {
    "previous_p50": 1200,
    "delta_ms": 50,
    "delta_percent": 4.2,
    "trend": "stable"
  }
}
```

### Success Criteria (from specification)
- ✅ SC-001: Search <3 seconds verified for all query types
- ✅ SC-002: Navigation <100ms verified for all transitions
- ✅ Memory baseline established (target <500MB)
- ✅ Results tracked over time for regression detection
- ✅ CPU utilization within bounds
- ✅ Cache performance optimized

### Dependencies
- Mock API responses (no external calls)
- SQLite cache populated with test data
- Memory profiler library available
- System has consistent load (test environment)

### Fixtures Required
- `.specify/fixtures/patents_1000.json` - 1000 patent records
- Mock USPTO API responses (pre-loaded)
- Test TUI environment initialized

### Commit Message
```
feat: add performance benchmark suite (Task 4.1)

Establish baselines and verify constitutional latency requirements:
- Search query → first result: <3 seconds (SC-001)
- Keyboard navigation → preview: <100ms (SC-002)
- Memory usage baseline <500MB under 1000+ results
- CPU utilization within bounds during operations
- Cache hit performance vs. miss delta measured

Benchmarks: 6 test scenarios, continuous regression detection
Metrics: p50/p95/p99 latencies, memory peak, CPU usage
Output: JSON reports with baseline comparison
```

---

## Task 5.1: Error Message Audit

**File**: `tests/test_error_handling.py`  
**Priority**: P1 - Constitutional (Actionable Errors)  
**Estimated Effort**: 6-8 hours  

### Goal
Audit all error messages to ensure they comply with RECON constitutional principles:
- 100% of errors provide exact reason
- 100% of errors include resolution steps
- Error voice is dry, factual, terse (no apologies)
- No generic "An error occurred" messages
- All errors are deterministic and testable

### Test Cases

#### 1. `test_network_timeout_error()`
**Assertion**: Network request times out
**Trigger**: Mock httpx client timeout after 5 seconds
**Expected Message**:
```
Search timeout: API request exceeded 5s limit
Resolution: Check internet connection; retry search
```

**Verifications**:
- ✅ Message includes exact reason (5s timeout)
- ✅ Resolution includes actionable step (check connection, retry)
- ✅ No apologies ("Sorry we couldn't...", "We encountered...")
- ✅ Terse (< 100 characters total)
- ✅ Factual tone (dry, no personality)

#### 2. `test_rate_limit_429_error()`
**Assertion**: API returns HTTP 429 (Rate Limited)
**Trigger**: Mock response with `Retry-After: 60` header
**Expected Message**:
```
Rate limited by USPTO (429): Retry in 60s
Resolution: Upgrade API tier at [link]; or wait 60 seconds
```

**Verifications**:
- ✅ Includes API source (USPTO)
- ✅ Exact wait time from Retry-After header
- ✅ API key guidance provided
- ✅ Links actionable (not vague)
- ✅ Deterministic (always same message for same scenario)

#### 3. `test_malformed_api_response_error()`
**Assertion**: API returns invalid JSON or missing required fields
**Trigger**: Mock USPTO response missing patent_id field
**Expected Message**:
```
Invalid patent record: missing required field 'patent_id'
Resolution: This is a data quality issue from USPTO; report to support
```

**Verifications**:
- ✅ Specifies exact missing field
- ✅ Identifies data source (USPTO)
- ✅ Suggests escalation path (report to support)
- ✅ Not user's fault (no "please check your query")

#### 4. `test_missing_image_error()`
**Assertion**: Patent image URL returns 404
**Trigger**: Mock image fetch returns HTTP 404
**Expected Message**:
```
Patent image unavailable: US10123456B2 has no digitized image in USPTO
Resolution: View on Patent Office website; or continue with claims/data
```

**Verifications**:
- ✅ Specific patent ID
- ✅ Exact reason (not digitized)
- ✅ Multiple resolution options
- ✅ Suggests reasonable alternative (use other tabs)

#### 5. `test_unsupported_terminal_error()`
**Assertion**: Terminal doesn't support image rendering
**Trigger**: Terminal capability detection returns unknown protocol
**Expected Message**:
```
Terminal doesn't support image protocol: detected 'dumb'
Resolution: Upgrade to Kitty/iTerm2/xterm-256color; or disable images in config
```

**Verifications**:
- ✅ Specific protocol detected
- ✅ Recommended terminals listed
- ✅ Configuration option provided
- ✅ User can take immediate action

#### 6. `test_corrupted_cache_error()`
**Assertion**: Cache database is corrupted
**Trigger**: Mock corrupted SQLite file
**Expected Message**:
```
Cache corrupted: database disk image malformed
Resolution: Run 'recon --clear-cache'; cache will rebuild automatically
```

**Verifications**:
- ✅ Exact SQLite error message included
- ✅ Exact command provided (not "clear the cache")
- ✅ Explains consequence (auto-rebuild)
- ✅ User can run command immediately

#### 7. `test_invalid_search_query_error()`
**Assertion**: Invalid search syntax
**Trigger**: Query with unmatched quotes or invalid operators
**Expected Message**:
```
Invalid search query: unmatched quote in '"AI patent'
Resolution: Fix syntax: use quotes in pairs, or escape with \
```

**Verifications**:
- ✅ Exact location of error (which character)
- ✅ Specific fix guidance (paired quotes, escape)
- ✅ Example shown
- ✅ Helps user understand syntax

#### 8. `test_missing_api_credentials_error()`
**Assertion**: API key not configured or invalid
**Trigger**: Mock config with empty/expired API key
**Expected Message**:
```
USPTO API key missing or invalid
Resolution: Set USPTO_API_KEY environment variable; get key at [link]
```

**Verifications**:
- ✅ Which API key is missing
- ✅ Exact env var name
- ✅ Link to get key
- ✅ Can be fixed immediately by user

#### 9. `test_no_results_found_error()`
**Assertion**: Search returns 0 results
**Expected Message**:
```
No patents found matching: "quantum entanglement refrigerators"
Resolution: Try simpler terms; remove phrases in quotes; check spelling
```

**Verifications**:
- ✅ Echoes back the query (shows search was understood)
- ✅ Suggests debugging steps
- ✅ Not an error per se (handled gracefully)

#### 10. `test_error_message_consistency_audit()`
**Assertion**: All error messages follow voice guidelines
**Checklist**:
- [ ] Scan all `.py` files for `raise` statements and error messages
- [ ] Verify no generic messages: "An error occurred", "Something went wrong", "Error"
- [ ] Verify all messages < 150 characters
- [ ] Verify all messages include reason + resolution
- [ ] Verify no apologies or conversational tone
- [ ] Verify all messages are deterministic (no random/unstable parts)

**Report**:
```
Total error messages scanned: 47
Generic messages found: 0 ✅
Messages with reason: 47/47 ✅
Messages with resolution: 47/47 ✅
Apologies/conversational tone: 0 ✅
Average length: 82 chars ✅
Determinism score: 100% ✅
```

### Error Audit Checklist
For each error message in the codebase:

```python
class ErrorAudit:
    def __init__(self, message: str):
        self.message = message
    
    def validate(self) -> Dict[str, bool]:
        return {
            "has_exact_reason": bool(self._extract_reason()),
            "has_resolution": bool(self._extract_resolution()),
            "is_terse": len(self.message) < 150,
            "is_deterministic": not self._contains_random(),
            "no_apologies": not self._contains_apologies(),
            "no_generic": not self._is_generic(),
        }
    
    def _extract_reason(self) -> str: ...
    def _extract_resolution(self) -> str: ...
    def _contains_random(self) -> bool: ...
    def _contains_apologies(self) -> bool: ...
    def _is_generic(self) -> bool: ...
```

### Success Criteria (from specification)
- ✅ 100% of errors provide reason + resolution (10/10 scenarios tested)
- ✅ Constitution principle verified: Dry, Actionable Error Voice
- ✅ No generic error messages in codebase
- ✅ All error messages deterministic
- ✅ Error voice audit passed (47/47 messages)
- ✅ Actionability verified per error type

### Dependencies
- Core error handling modules implemented
- CLI error messages finalized
- TUI error display logic complete
- API client error handling complete

### Fixtures Required
- Mock API errors: 429, 404, timeout, malformed JSON
- Mock corrupted cache file
- Mock terminal capability detection (unsupported)
- Mock invalid search queries

### Commit Message
```
feat: add error message audit suite (Task 5.1)

Audit all error messages for clarity, actionability, and voice consistency:
- 100% of errors provide exact reason + resolution steps
- Error voice is dry, factual, terse (constitutional requirement)
- No generic "An error occurred" messages
- 10 error scenarios tested end-to-end
- 47 error messages audited for compliance

Tests: 10 test cases + consistency audit
Audit Results: 100% compliance with error voice guidelines
Errors Covered: Network, rate limit, malformed response, missing image,
               unsupported terminal, corrupted cache, invalid query,
               missing credentials, no results, message voice
```

---

## Execution Order & Dependencies

### Sequencing

```
┌─────────────────────────────────────────┐
│ Phase C: Advanced Testing               │
│ Parallel to Dev Phases 4-5              │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
Task 3.3        Task 4.1        Task 5.1
Cache           Performance     Error
Validation      Benchmarks      Handling
(8-10h)         (10-12h)        (6-8h)
    │               │               │
    └───────────────┴───────────────┘
            │
            ▼
    Can execute in parallel
    (no blocking dependencies)
```

### Dependency Analysis

| Task | Depends On | Blocked By | Notes |
|------|-----------|------------|-------|
| 3.3 (Cache) | storage/ module | None | Can run anytime |
| 4.1 (Performance) | core/ module + mocks | None | Needs stable codebase |
| 5.1 (Error) | All error paths | None | Can run in parallel |

### Recommended Execution Strategy

**Option A: Parallel (Recommended)**
- Start all 3 tasks simultaneously
- Each can progress independently
- Total time: ~12 hours (longest task) vs. 24-30 hours sequentially
- Risk: Shared codebase conflicts during testing

**Option B: Sequential**
- Task 3.3 first (storage layer foundation)
- Task 4.1 second (depends on stable cache)
- Task 5.1 last (depends on all error paths)
- Total time: 24-30 hours
- Risk: None, but longer timeline

**Option C: Recommended - Staggered**
- Day 1: Start Task 3.3 + Task 5.1 (different modules)
- Day 2: Add Task 4.1 once 3.3 baseline established
- Total time: ~15 hours across 2-3 days
- Risk: Minimal, controlled progression

---

## Test Fixtures Required

All fixtures should be placed in `.specify/fixtures/`:

```
.specify/fixtures/
├── patents_1000.json              # 1000 patent records (Task 4.1)
├── cache_test_data.db             # SQLite cache for Task 3.3
├── api_responses/
│   ├── uspto_valid_response.json
│   ├── uspto_rate_limit_429.json
│   ├── uspto_malformed.json
│   └── api_timeout_scenario.json
├── terminals/
│   ├── kitty_capabilities.json
│   ├── iterm2_capabilities.json
│   ├── dumb_terminal.json
│   └── unsupported_protocol.json
└── corrupted_cache/
    ├── truncated.db               # Corrupted database for Task 3.3
    └── malformed_json.db
```

---

## Success Criteria Summary

### Task 3.3 (Cache Validation)
- ✅ Document content cached indefinitely
- ✅ Metadata refreshed every 30 days
- ✅ Citations append-only (never overwritten)
- ✅ Corrupted cache recoverable
- ✅ Thread-safe concurrent access
- ✅ 100% cache module coverage

### Task 4.1 (Performance Benchmarks)
- ✅ SC-001: Search <3 seconds verified
- ✅ SC-002: Navigation <100ms verified
- ✅ Memory baseline <500MB under load
- ✅ CPU utilization within bounds
- ✅ Regression detection established
- ✅ Historical tracking capability

### Task 5.1 (Error Message Audit)
- ✅ 100% of errors: reason + resolution
- ✅ Error voice: dry, factual, terse
- ✅ No generic messages in codebase
- ✅ All errors deterministic
- ✅ 10 error scenarios tested
- ✅ Constitutional compliance verified

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review both spec documents thoroughly
- [ ] Verify storage/ module complete
- [ ] Verify core/ module stable
- [ ] Identify all error paths in codebase
- [ ] Create fixture directory structure
- [ ] Set up performance measurement tools

### Task 3.3 Implementation
- [ ] Create `tests/test_cache_validation.py`
- [ ] Implement all 6 test cases
- [ ] Verify assertions against storage/ module
- [ ] Create cache fixtures (valid + corrupted)
- [ ] Run tests in isolation
- [ ] Commit with message format

### Task 4.1 Implementation
- [ ] Create `tests/test_performance.py`
- [ ] Implement all 6 benchmark scenarios
- [ ] Generate JSON report format
- [ ] Establish baseline metrics
- [ ] Create regression detection logic
- [ ] Commit with message format

### Task 5.1 Implementation
- [ ] Create `tests/test_error_handling.py`
- [ ] Implement all 10 error scenarios
- [ ] Create error message consistency audit
- [ ] Scan codebase for all error messages
- [ ] Document audit results
- [ ] Commit with message format

### Post-Implementation
- [ ] All tests passing locally
- [ ] Coverage metrics verified
- [ ] Performance baselines established
- [ ] Error audit complete
- [ ] Documentation updated
- [ ] Phase C marked complete

---

## Testing Commands

```bash
# Run all Phase C tests
pytest tests/test_cache_validation.py \
       tests/test_performance.py \
       tests/test_error_handling.py -v

# Run with coverage
pytest tests/test_cache_validation.py \
       tests/test_performance.py \
       tests/test_error_handling.py \
       --cov=storage --cov=core --cov=cli \
       --cov-report=html

# Run performance benchmarks only
pytest tests/test_performance.py -v --benchmark-json=results.json

# Run error audit
pytest tests/test_error_handling.py::test_error_message_consistency_audit -v

# Generate reports
python tests/evaluation_report.py --format=markdown > EVALUATION_PHASE_C.md
python tests/evaluation_report.py --format=json > evaluation_phase_c.json
```

---

## Related Specifications

- `.specify/docs/evaluation-framework.md` - Evaluation framework overview
- `.specify/tasks/EVALUATION_TASKS.md` - Full task breakdown
- `.specify/docs/spec.md` - Feature requirements
- `.specify/docs/constitution.md` - Core principles (error voice, performance, data integrity)

---

## Notes

1. **Performance Tests**: Run on consistent hardware/network to minimize variance. Consider separate CI pipeline for benchmarks.

2. **Cache Tests**: Use real SQLite instance (not mock) to test actual behavior. Include transaction testing for concurrency.

3. **Error Tests**: Test both message content and delivery mechanism (CLI vs. TUI display). Verify error doesn't crash application.

4. **Fixtures**: Pre-generate large datasets (1000 patents) to avoid test data generation overhead.

5. **Regression**: Store baseline metrics in version control for comparison. Alert on >5% performance regression.

---

## Document Information

**Created**: 2026-05-13  
**Phase**: Advanced Testing (Phase C)  
**Owner**: Development Team  
**Status**: Ready for Implementation  
**Next Steps**: Begin implementation of Task 3.3  

