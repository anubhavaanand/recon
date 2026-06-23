# RECON Monitoring & Alerting Specification v1.0.0

**Project:** RECON — Terminal-Native Patent Research Tool  
**Version:** 1.0.0  
**Date:** 2026-06-22  
**Classification:** Internal — Agent Guidance Document  
**Review Cycle:** Quarterly or after every release  

---

## 1. Document Metadata

| Field | Value |
|-------|-------|
| **Project** | RECON |
| **Stack** | Python 3.12+, Textual (TUI), Typer (CLI), httpx, SQLite |
| **Infra** | Self-hosted / local-only (single-process desktop application) |
| **Monitoring Paradigm** | Telemetry + structured logs (no traditional server monitoring) |
| **Expected Usage** | 10–100 searches/day per user, 1 concurrent user per installation |
| **Tooling** | Python `logging` (stdlib), JSON structured logs, optional: Prometheus pushgateway for fleet deployments |

> **Important:** RECON is a **local desktop application**, not a SaaS or server. Traditional infrastructure monitoring (CPU alerts, load balancers) does not apply. This spec adapts SRE principles to a terminal-native, single-user tool with optional fleet telemetry.

---

## 2. System Context & Trust Boundary

### 2.1 Deployment Model

```
+-------------------------------------------------------------+
|                        USER MACHINE                          |
|  +-------------+    +--------------+    +-----------------+ |
|  |   Terminal  |--->|    RECON     |--->|  External APIs   | |
|  |  (Kitty/etc)|<---|  (Python 3.12|<---|  USPTO/WIPO/EPO  | |
|  +-------------+    |   + Textual) |    +-----------------+ |
|                     +--------------+                         |
|                            |                                 |
|                     +------+------+                          |
|                     |  ~/.cache/  |                          |
|                     |    recon/   |                          |
|                     | (SQLite DB) |                          |
|                     +-------------+                          |
|                            |                                 |
|                     +------+------+                          |
|                     |~/.config/   |                          |
|                     |recon/       |                          |
|                     |config.toml  |                          |
|                     +-------------+                          |
+-------------------------------------------------------------+
```

### 2.2 Trust Boundary

| Boundary | Description | Monitoring Implication |
|----------|-------------|------------------------|
| **User OS** | Single-user machine | No multi-tenant isolation metrics needed |
| **RECON Process** | Python process with asyncio event loop | Monitor event loop blocking, memory growth |
| **External APIs** | USPTO, WIPO, EPO, Google Patents, Lens | Monitor latency, error rates, rate limit proximity |
| **Local Filesystem** | `~/.cache/recon/`, `~/.config/recon/` | Monitor disk usage, config corruption |

---

## 3. Golden Signals

Adapted from Google's Four Golden Signals for a local CLI/TUI application.

### 3.1 Signal Definitions

| Signal | Metric Name | Description | Collection Method |
|--------|-------------|-------------|-------------------|
| **Latency** | `recon_search_duration_seconds` | Time from query submission to result display (CLI) or result list population (TUI) | In-app timer around `search_all()` |
| **Latency** | `recon_tab_switch_duration_ms` | Time from tab activation to content render | In-app timer around `_load_active_tab()` |
| **Traffic** | `recon_searches_total` | Count of search queries executed | Counter incremented per `search_all()` call |
| **Traffic** | `recon_api_calls_total` | Count of external API calls by source | Counter per client call, labeled by `source={uspto,wipo,epo,google,lens}` |
| **Errors** | `recon_search_errors_total` | Count of failed searches | Counter, labeled by `error_type={api_timeout,rate_limit,parse_error,network_error,config_missing}` |
| **Errors** | `recon_api_error_rate` | Ratio of failed API calls to total calls | Derived: `errors_total / calls_total` |
| **Saturation** | `recon_cache_hit_ratio` | Ratio of cache hits to total search requests | Derived: `cache_hits / (cache_hits + cache_misses)` |
| **Saturation** | `recon_rate_limit_proximity` | Percentage of rate limit consumed (0.0–1.0) | Gauge per API source, updated after each call |
| **Saturation** | `recon_memory_usage_mb` | RSS memory of RECON process | `psutil.Process().memory_info().rss / 1024 / 1024` |

### 3.2 Golden Signal Thresholds

| Signal | Good | Warning | Critical |
|--------|------|---------|----------|
| Search latency (cold) | < 3s | 3–5s | > 5s |
| Search latency (warm/cache) | < 100ms | 100–300ms | > 300ms |
| Tab switch latency | < 50ms | 50–100ms | > 100ms |
| API error rate | < 1% | 1–5% | > 5% |
| Cache hit ratio | > 80% | 50–80% | < 50% |
| Rate limit proximity | < 50% | 50–76% | > 76% (24% headroom violated) |
| Memory usage | < 256MB | 256–512MB | > 512MB |

---

## 4. Business Metrics

RECON is a single-user research tool; "business metrics" translate to **user productivity and research quality indicators**.

| Metric Name | Description | Target | Collection |
|-------------|-------------|--------|------------|
| `recon_patents_viewed_per_session` | Average patents opened in preview per search session | > 3 | Event log on tab activation |
| `recon_collection_saves_per_session` | Patents saved to collection per session | > 1 | Event log on `s` hotkey |
| `recon_export_operations_total` | Export operations by format | N/A | Counter, labeled by `format={json,csv,bibtex,markdown,pdf}` |
| `recon_reader_mode_activations` | Times reader mode opened per session | > 1 | Event log on `r` hotkey |
| `recon_sources_used_per_search` | Number of API sources queried per search | > 2 | Gauge per `search_all()` call |
| `recon_intelligence_signals_avg` | Average cross-reference signals per patent | > 2 | Gauge from scoring output |
| `recon_session_duration_seconds` | Time from TUI open to quit | 5–30 min | Timer on app mount/exit |
| `recon_configured_sources` | Count of API keys configured | >= 2 | Gauge from config file scan |

---

## 5. Infrastructure Metrics

For a local desktop app, infrastructure monitoring focuses on **process health and resource consumption**, not server clusters.

| Metric Name | Description | Warning Threshold | Critical Threshold |
|-------------|-------------|-------------------|-------------------|
| `recon_cpu_percent` | CPU usage of RECON process | > 25% sustained | > 50% sustained |
| `recon_memory_mb` | RSS memory in MB | > 256MB | > 512MB |
| `recon_sqlite_db_size_mb` | Size of cache database | > 100MB | > 1GB |
| `recon_cache_entries_total` | Number of cached search results | > 10,000 | > 100,000 |
| `recon_cache_oldest_entry_age_days` | Age of oldest cache entry | > 30 days | > 60 days |
| `recon_disk_free_gb` | Free space on partition containing `~/.cache/recon/` | < 5GB | < 1GB |
| `recon_open_file_descriptors` | FD count (Unix) | > 64 | > 256 |
| `recon_event_loop_blocked_ms` | Time event loop was blocked (Textual-specific) | > 16ms | > 100ms |

**Collection:** Use `psutil` (optional dependency, v0.3.0+) or `/proc` filesystem parsing on Linux.

---

## 6. Alert Rules

### 6.1 Alert Rule Table

| Metric | Condition | Threshold | Severity | Action | Runbook |
|--------|-----------|-----------|----------|--------|---------|
| `recon_search_duration_seconds` | `avg_over_time` > 5s | 5s | **P1** | Log warning, suggest cache warm-up | RB-001 |
| `recon_api_error_rate` | `rate` > 5% | 5% | **P0** | Display `ERR:` to user, enable fallback mocks | RB-002 |
| `recon_rate_limit_proximity` | > 0.76 | 76% | **P1** | Throttle requests, display warning banner | RB-003 |
| `recon_memory_mb` | > 512 | 512MB | **P1** | Suggest cache purge, log for debugging | RB-004 |
| `recon_sqlite_db_size_mb` | > 1024 | 1GB | **P2** | Suggest `recon cache clear` command | RB-005 |
| `recon_disk_free_gb` | < 1 | 1GB | **P0** | Halt cache writes, display `ERR: Disk full` | RB-006 |
| `recon_event_loop_blocked_ms` | > 100 | 100ms | **P1** | Log blocking call stack trace | RB-007 |
| `recon_cache_hit_ratio` | < 0.50 | 50% | **P2** | Log, investigate cache invalidation logic | RB-008 |
| `recon_config_missing` | == 0 | 0 keys | **P2** | Display setup wizard on first launch | RB-009 |
| `recon_corrupt_cache_detected` | == 1 | boolean | **P0** | Auto-rebuild cache from scratch | RB-010 |

### 6.2 Severity Definitions

| Severity | Response Time | Who | Action |
|----------|--------------|-----|--------|
| **P0 — Critical** | Immediate | User (self-healing) | Tool displays error, may disable feature automatically |
| **P1 — High** | < 1 hour | User | Warning displayed, manual intervention suggested |
| **P2 — Medium** | < 24 hours | User | Logged, surfaced in `--diagnostics` flag |
| **P3 — Low** | Next release | Developer | Backlog item, no user impact |

> **Note:** RECON has no on-call rotation. Alerts are **self-service** — displayed in the TUI footer, logged to `~/.cache/recon/recon.log`, and optionally pushed to a monitoring endpoint for fleet deployments.

---

## 7. On-Call Runbooks

### RB-001: Slow Search

**Symptom:** `recon_search_duration_seconds > 5s`  
**Impact:** User experience degraded, search feels sluggish  

**Steps:**
1. Check if query is cacheable (repeated query should be < 100ms)
2. If cold cache: Verify external API latency with `recon diagnostics --api-ping`
3. If warm cache still slow: Check `recon_event_loop_blocked_ms` for blocking I/O in TUI thread
4. If APIs slow: Enable `--offline` mode to force cache-only search
5. If persistent: Suggest cache purge with `recon cache clear`

**Resolution Criteria:** Search latency returns to < 3s for cold, < 100ms for warm.

---

### RB-002: API Degradation

**Symptom:** `recon_api_error_rate > 5%`  
**Impact:** Search results incomplete or missing  

**Steps:**
1. Identify failing source from `recon_api_calls_total{status="error"}` labels
2. Check source-specific error: timeout (increase backoff), 429 (rate limit hit), 5xx (source down)
3. Temporarily disable failing source in `config.toml` under `[sources]` section
4. Fall back to remaining sources + cache
5. Notify user with dry error voice: `ERR: USPTO API unavailable. Using WIPO + cache.`

**Resolution Criteria:** Error rate < 1% for 5 consecutive searches.

---

### RB-003: Rate Limit Proximity

**Symptom:** `recon_rate_limit_proximity > 0.76` for any source  
**Impact:** Risk of 429 errors, search interruption  

**Steps:**
1. Display warning in TUI footer: `RATE: USPTO 89% — throttling active`
2. Enable automatic request throttling (increase inter-request delay by 2x)
3. Prioritize cache hits over live API calls
4. If > 95%: Halt live calls for that source, cache-only mode
5. Reset counter at source's window reset (daily for WIPO, per-minute for USPTO)

**Resolution Criteria:** Rate limit proximity < 50% after window reset.

---

### RB-004: Memory Pressure

**Symptom:** `recon_memory_mb > 512`  
**Impact:** System slowdown, potential OOM kill  

**Steps:**
1. Check `recon_sqlite_db_size_mb` — large cache may cause memory bloat from query result caching
2. Run `recon cache clear --older-than 30` to purge old entries
3. Check for memory leaks: `recon_memory_mb` should drop after cache clear
4. If still high: Check for unclosed `httpx.AsyncClient` connections
5. If leak confirmed: Restart RECON, file bug with `--diagnostics` output

**Resolution Criteria:** Memory < 256MB after cache clear.

---

### RB-005: Cache Bloat

**Symptom:** `recon_sqlite_db_size_mb > 1024`  
**Impact:** Disk usage, slower cache queries  

**Steps:**
1. Run `recon cache stats` to see entry count and age distribution
2. Purge entries older than 30 days: `recon cache clear --older-than 30`
3. If still large: Purge by query frequency (remove queries with < 3 accesses)
4. Vacuum SQLite: `recon cache vacuum` (reclaims disk space)
5. If recurrent: Reduce default TTL from 30 days to 14 days in config

**Resolution Criteria:** DB size < 100MB or < 10,000 entries.

---

### RB-006: Disk Exhaustion

**Symptom:** `recon_disk_free_gb < 1`  
**Impact:** Cache writes fail, config cannot be saved, exports fail  

**Steps:**
1. Halt all cache writes immediately (set `cache_mode = "read-only"`)
2. Display `ERR: Disk space critical. Cache disabled.`
3. Suggest cache purge or moving cache directory to another partition
4. Disable PDF export (largest temp files) until space available
5. If user frees space: Re-enable cache writes automatically

**Resolution Criteria:** Disk free > 5GB.

---

### RB-007: Event Loop Block

**Symptom:** `recon_event_loop_blocked_ms > 100`  
**Impact:** TUI freezes, keyboard input delayed, async tasks stall  

**Steps:**
1. Identify blocking call from stack trace in logs
2. Common culprits: synchronous SQLite queries on large result sets, Pillow image processing without `run_in_executor`
3. If SQLite blocking: Switch to `aiosqlite` (v0.3.0) or add query pagination
4. If image processing: Offload to `asyncio.get_event_loop().run_in_executor()`
5. If rapidfuzz on large corpus: Add result limit or pre-filter

**Resolution Criteria:** No blocking events > 16ms for 1 minute.

---

### RB-008: Cache Inefficiency

**Symptom:** `recon_cache_hit_ratio < 50%`  
**Impact:** Unnecessary API calls, slower searches, rate limit consumption  

**Steps:**
1. Check if queries are too specific (unique strings that never repeat)
2. Verify cache is being checked before API calls in `core/search.py`
3. Check for cache invalidation bugs (entries deleted prematurely)
4. If cache working correctly: User behavior may be exploratory (many unique queries) — expected
5. If bug: Review `storage/cache.py` `get_cached_results()` logic

**Resolution Criteria:** Cache hit ratio > 80% for repeated queries.

---

### RB-009: No API Keys

**Symptom:** `recon_configured_sources == 0`  
**Impact:** All searches return mock data or empty results  

**Steps:**
1. On first launch, display inline setup wizard (not modal)
2. Guide user to: `recon config set --uspto-key <KEY>`
3. Provide links to USPTO/WIPO developer portals in help text
4. Allow `--demo` mode with mock data for evaluation
5. Cache demo searches so user sees value before configuring keys

**Resolution Criteria:** >= 1 source configured.

---

### RB-010: Cache Corruption

**Symptom:** `recon_corrupt_cache_detected == 1` (SQLite integrity check fails)  
**Impact:** Searches may crash, data loss  

**Steps:**
1. Immediately back up corrupt DB to `~/.cache/recon/cache.db.bak.<timestamp>`
2. Run `PRAGMA integrity_check` to confirm corruption extent
3. If repairable: `PRAGMA writable_schema = 1;` + manual repair (advanced)
4. If unrepairable: Delete and rebuild cache DB from scratch
5. Log corruption cause (power loss, disk full, bug) for post-mortem

**Resolution Criteria:** New cache DB passes `PRAGMA integrity_check`.

---

## 8. Logging Strategy

### 8.1 Log Levels & Usage

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Development, trace-level detail | `DEBUG: Cache miss for query_hash=abc123` |
| `INFO` | Normal operations, lifecycle events | `INFO: Search completed | sources=3 | results=15 | latency=1.2s` |
| `WARNING` | Degraded but functional | `WARNING: USPTO API timeout after 8s, fallback to cache` |
| `ERROR` | Feature failure, user-visible | `ERROR: Cache write failed | disk_full=True | path=~/.cache/recon/` |
| `CRITICAL` | Tool cannot function, data at risk | `CRITICAL: SQLite corruption detected | rebuilding cache` |

### 8.2 Structured Logging Format

All logs MUST be JSON Lines (JSONL) for machine parsing:

```json
{
  "timestamp": "2026-06-22T19:32:00Z",
  "level": "INFO",
  "component": "search",
  "event": "search_completed",
  "query_hash": "sha256:abc123...",
  "sources": ["uspto", "wipo"],
  "results_count": 15,
  "latency_ms": 1200,
  "cache_hit": false,
  "session_id": "recon-20260622-abc123",
  "version": "0.2.0"
}
```

**Required fields for every log entry:**
- `timestamp` — ISO 8601 UTC
- `level` — Log level uppercase
- `component` — One of: `cli`, `tui`, `search`, `cache`, `client`, `export`, `config`
- `event` — Snake_case action name
- `session_id` — Unique per RECON invocation (UUID4, first 8 chars)
- `version` — RECON version string

**Prohibited in logs:**
- API keys or secrets (mask as `***`)
- Full patent abstracts (log hash only)
- User search queries in plaintext (log `query_hash` only)
- Stack traces at `INFO` or below

### 8.3 Log Locations

| Environment | Path | Rotation |
|-------------|------|----------|
| Default | `~/.cache/recon/recon.log` | 10MB, 5 backups |
| Debug mode | `~/.cache/recon/recon.debug.log` | 50MB, 3 backups |
| `--diagnostics` | stdout (JSONL) | N/A |

### 8.4 Log Rotation Configuration

```python
# Python logging config (stdlib)
import logging
from logging.handlers import RotatingFileHandler
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "component": getattr(record, "component", "unknown"),
            "event": getattr(record, "event", record.msg),
            "message": record.getMessage(),
            "session_id": SESSION_ID,
            "version": VERSION,
        }
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        return json.dumps(log_obj)

handler = RotatingFileHandler(
    "~/.cache/recon/recon.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding="utf-8"
)
handler.setFormatter(JSONFormatter())
```

---

## 9. Dashboards

### 9.1 Dashboard: RECON Session Overview

**Purpose:** Real-time view of current session health  
**Refresh:** On event (not time-based, since it's local)  
**Display:** `--diagnostics` flag or `recon stats` command  

| Panel | Metric | Visualization |
|-------|--------|---------------|
| Search Latency | `recon_search_duration_seconds` | Histogram, last 10 searches |
| API Health | `recon_api_error_rate` by source | Bar chart, current session |
| Cache Efficiency | `recon_cache_hit_ratio` | Gauge (0–100%) |
| Rate Limit Status | `recon_rate_limit_proximity` | 5 gauges (one per source) |
| Memory Usage | `recon_memory_mb` | Line chart, session timeline |
| Search Volume | `recon_searches_total` | Counter, session total |
| Export Activity | `recon_export_operations_total` | Bar chart by format |

### 9.2 Dashboard: API Performance

**Purpose:** External API health and latency trends  
**Display:** `--diagnostics --api`  

| Panel | Metric |
|-------|--------|
| Latency by Source | `recon_search_duration_seconds` split by `source` |
| Error Rate by Source | `recon_api_error_rate` |
| Rate Limit Burn | `recon_rate_limit_proximity` timeline |
| Response Code Distribution | `recon_api_calls_total` by `status_code` |

### 9.3 Dashboard: Cache Analytics

**Purpose:** Cache effectiveness and storage health  
**Display:** `recon cache stats`  

| Panel | Metric |
|-------|--------|
| Hit Ratio Trend | `recon_cache_hit_ratio` over time |
| DB Size | `recon_sqlite_db_size_mb` |
| Entry Count | `recon_cache_entries_total` |
| Age Distribution | Histogram of entry ages |
| Top Queries | Most frequent `query_hash` |

---

## 10. SLIs & SLOs

### 10.1 Service Level Indicators

| SLI ID | Description | Metric | Measurement Window |
|--------|-------------|--------|-------------------|
| **SLI-001** | Search latency (cold cache) | `recon_search_duration_seconds` | Per search, 7-day rolling |
| **SLI-002** | Search availability | Ratio of successful searches to total | Per session, 30-day rolling |
| **SLI-003** | TUI responsiveness | `recon_tab_switch_duration_ms` | Per tab switch, 7-day rolling |
| **SLI-004** | Cache effectiveness | `recon_cache_hit_ratio` | Per session, 30-day rolling |
| **SLI-005** | API reliability | `1 - recon_api_error_rate` | Per source, 7-day rolling |

### 10.2 Service Level Objectives

| SLO ID | SLI | Target | Error Budget | Consequence of Breach |
|--------|-----|--------|--------------|----------------------|
| **SLO-001** | SLI-001 | 95% of cold searches < 3s | 5% of searches may exceed | Investigate API latency or add parallelization |
| **SLO-002** | SLI-002 | 99% of searches succeed | 1% failure rate allowed | Enable automatic fallback to cache + mocks |
| **SLO-003** | SLI-003 | 99% of tab switches < 50ms | 1% may exceed | Optimize widget render path, investigate blocking |
| **SLO-004** | SLI-004 | Cache hit ratio > 80% | 20% miss rate allowed | Review cache TTL, query normalization |
| **SLO-005** | SLI-005 | Per-source API availability > 95% | 5% downtime allowed | Disable failing source, alert user |

---

## 11. Error Budget Policy

### 11.1 Budget Calculation

Error budget = `1 - SLO target`

| SLO | Budget | Period | Burn Rate Alert |
|-----|--------|--------|-----------------|
| SLO-001 (Latency) | 5% of searches > 3s | 30 days | Burn > 2x normal = investigate |
| SLO-002 (Availability) | 1% search failure | 30 days | Burn > 5x = emergency fallback mode |
| SLO-003 (Responsiveness) | 1% tab switches > 50ms | 30 days | Burn > 3x = profile TUI thread |

### 11.2 Budget Exhaustion Actions

| Budget Remaining | Action |
|-----------------|--------|
| > 50% | Normal operations |
| 25–50% | Increase monitoring frequency, review recent changes |
| 10–25% | Freeze new features, prioritize reliability fixes |
| < 10% | Halt releases, all hands on reliability, enable safe mode |
| 0% (exhausted) | Automatic safe mode: cache-only, single source, reduced features |

### 11.3 Safe Mode Behavior

When error budget is exhausted or critical alerts fire:
- Disable live API calls (cache-only search)
- Limit results to top 10 per source
- Disable image rendering (text-only)
- Disable cross-reference intelligence (reduces API calls)
- Display banner: `SAFE MODE: Limited functionality. Check diagnostics.`
- Log all actions at `WARNING` level

---

## 12. Tool-Specific Config Snippets

### 12.1 Prometheus Pushgateway (Fleet Deployments)

If RECON is deployed in an enterprise environment with multiple users, push metrics to a central Prometheus instance:

```yaml
# prometheus-rules.yml
# Place in ~/.config/recon/monitoring/prometheus.yml or fleet config

groups:
  - name: recon_alerts
    rules:
      - alert: ReconHighSearchLatency
        expr: avg_over_time(recon_search_duration_seconds[5m]) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "RECON search latency high for {{ $labels.instance }}"
          description: "Average search latency is {{ $value }}s over 5m"

      - alert: ReconAPIErrorRate
        expr: rate(recon_search_errors_total[5m]) / rate(recon_searches_total[5m]) > 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "RECON API error rate elevated"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: ReconRateLimitProximity
        expr: recon_rate_limit_proximity > 0.76
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "RECON rate limit proximity high for {{ $labels.source }}"
          description: "Rate limit at {{ $value | humanizePercentage }}"

      - alert: ReconMemoryHigh
        expr: recon_memory_mb > 512
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "RECON memory usage high"
          description: "Memory at {{ $value }}MB"

      - alert: ReconDiskFull
        expr: recon_disk_free_gb < 1
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "RECON disk space critical"
          description: "Only {{ $value }}GB free"
```

### 12.2 Python Metrics Collection (In-App)

```python
# core/metrics.py
# Metrics collection module for RECON
# Zero external dependencies — uses stdlib + optional psutil

import time
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from enum import Enum

class Severity(Enum):
    P0 = "critical"
    P1 = "high"
    P2 = "medium"
    P3 = "low"

@dataclass
class MetricSnapshot:
    timestamp: str
    session_id: str
    version: str
    search_latency_ms: float
    cache_hit_ratio: float
    memory_mb: Optional[float]
    api_error_rate: float
    rate_limit_proximity: Dict[str, float]
    active_alerts: List[Dict]

class MetricsCollector:
    """Collects and exposes RECON metrics. No external deps."""

    def __init__(self, session_id: str, version: str):
        self.session_id = session_id
        self.version = version
        self.search_count = 0
        self.search_errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls: Dict[str, Dict] = {}
        self.latencies: List[float] = []

    def record_search(self, latency_ms: float, cache_hit: bool, error: bool = False):
        self.search_count += 1
        self.latencies.append(latency_ms)
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        if error:
            self.search_errors += 1

    def record_api_call(self, source: str, success: bool, rate_limit_used: float):
        if source not in self.api_calls:
            self.api_calls[source] = {"total": 0, "errors": 0, "rate_limit_max": 0.0}
        self.api_calls[source]["total"] += 1
        if not success:
            self.api_calls[source]["errors"] += 1
        self.api_calls[source]["rate_limit_max"] = max(
            self.api_calls[source]["rate_limit_max"], rate_limit_used
        )

    def get_memory_mb(self) -> Optional[float]:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return None

    def snapshot(self) -> MetricSnapshot:
        total_cache = self.cache_hits + self.cache_misses
        cache_ratio = self.cache_hits / total_cache if total_cache > 0 else 0.0

        total_api = sum(s["total"] for s in self.api_calls.values())
        total_api_errors = sum(s["errors"] for s in self.api_calls.values())
        api_error_rate = total_api_errors / total_api if total_api > 0 else 0.0

        rate_limits = {
            src: data["rate_limit_max"] 
            for src, data in self.api_calls.items()
        }

        alerts = self._evaluate_alerts(cache_ratio, api_error_rate, rate_limits)

        return MetricSnapshot(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            session_id=self.session_id,
            version=self.version,
            search_latency_ms=sum(self.latencies[-10:]) / min(len(self.latencies), 10) if self.latencies else 0,
            cache_hit_ratio=cache_ratio,
            memory_mb=self.get_memory_mb(),
            api_error_rate=api_error_rate,
            rate_limit_proximity=rate_limits,
            active_alerts=alerts
        )

    def _evaluate_alerts(self, cache_ratio: float, api_error_rate: float, 
                         rate_limits: Dict[str, float]) -> List[Dict]:
        alerts = []

        if api_error_rate > 0.05:
            alerts.append({
                "metric": "recon_api_error_rate",
                "value": api_error_rate,
                "threshold": 0.05,
                "severity": Severity.P0.value,
                "runbook": "RB-002"
            })

        for source, proximity in rate_limits.items():
            if proximity > 0.76:
                alerts.append({
                    "metric": "recon_rate_limit_proximity",
                    "source": source,
                    "value": proximity,
                    "threshold": 0.76,
                    "severity": Severity.P1.value,
                    "runbook": "RB-003"
                })

        if cache_ratio < 0.5 and (self.cache_hits + self.cache_misses) > 10:
            alerts.append({
                "metric": "recon_cache_hit_ratio",
                "value": cache_ratio,
                "threshold": 0.5,
                "severity": Severity.P2.value,
                "runbook": "RB-008"
            })

        return alerts

    def write_snapshot(self, path: str = "~/.cache/recon/metrics.jsonl"):
        snap = self.snapshot()
        expanded = os.path.expanduser(path)
        os.makedirs(os.path.dirname(expanded), exist_ok=True)
        with open(expanded, "a") as f:
            f.write(json.dumps(asdict(snap)) + "\n")
```

### 12.3 Textual TUI Alert Banner Widget

```python
# tui/widgets/alert_banner.py
# Inline alert banner for TUI (NOT modal — constitution compliant)

from textual.widgets import Static
from textual.reactive import reactive

class AlertBanner(Static):
    """Displays active alerts as an inline banner at top of screen.

    Constitution compliant: No modal dialog. Inline only.
    Dismissed automatically when alerts clear or via 'a' hotkey toggle.
    """

    alerts = reactive(list)

    def watch_alerts(self, alerts: list):
        if not alerts:
            self.styles.display = "none"
            return

        self.styles.display = "block"
        lines = []
        for alert in alerts:
            severity = alert["severity"].upper()
            icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "HIGH" else "🔵"
            lines.append(f"{icon} [{severity}] {alert['metric']}: {alert['value']:.2f} (threshold: {alert['threshold']}) | Runbook: {alert['runbook']}")

        self.update("\n".join(lines))

    CSS = """
    AlertBanner {
        display: none;
        height: auto;
        background: $surface-darken-2;
        color: $text;
        padding: 1;
        border-bottom: solid $warning;
    }
    """
```

### 12.4 CLI Diagnostics Command

```python
# cli/diagnostics.py
# Standalone diagnostics for troubleshooting

import typer
import json
from pathlib import Path
from datetime import datetime, timedelta

diagnostics_app = typer.Typer(help="RECON diagnostics and monitoring")

@diagnostics_app.command()
def stats(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    api_ping: bool = typer.Option(False, "--api-ping", help="Ping all configured APIs")
):
    """Show current session statistics and health."""
    from core.metrics import MetricsCollector
    from storage.cache import CacheDatabase
    from core.config import Config

    config = Config.load()
    cache = CacheDatabase()

    # Build diagnostics report
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "0.2.0",
        "config": {
            "uspto_configured": bool(config.uspto_key),
            "wipo_configured": True,  # No key needed
            "epo_configured": bool(config.epo_consumer_key),
        },
        "cache": {
            "db_size_mb": cache.get_db_size_mb(),
            "entries_total": cache.get_entry_count(),
            "oldest_entry_days": cache.get_oldest_entry_age_days(),
        },
        "system": {
            "python_version": "3.12+",
            "platform": "linux",  # Detected at runtime
        }
    }

    if json_output:
        typer.echo(json.dumps(report, indent=2))
    else:
        typer.echo("═" * 50)
        typer.echo("  RECON Diagnostics")
        typer.echo("═" * 50)
        for section, data in report.items():
            if isinstance(data, dict):
                typer.echo(f"\n[{section}]")
                for k, v in data.items():
                    typer.echo(f"  {k}: {v}")
            else:
                typer.echo(f"{section}: {data}")

    if api_ping:
        typer.echo("\n[API Ping]")
        # Implementation: ping each configured API with timeout
        # Display latency per source
```

---

## 13. Implementation Checklist

### 13.1 Pre-Release (v0.3.0)

| # | Task | File | Effort | Priority |
|---|------|------|--------|----------|
| 1 | Implement `core/metrics.py` collector | `core/metrics.py` | M | P1 |
| 2 | Add JSON structured logging | `core/logging_config.py` | S | P1 |
| 3 | Integrate metrics into search pipeline | `core/search.py` | S | P1 |
| 4 | Add AlertBanner widget to TUI | `tui/widgets/alert_banner.py` | S | P1 |
| 5 | Add `recon diagnostics` CLI command | `cli/diagnostics.py` | S | P2 |
| 6 | Add `recon cache stats/clear` commands | `cli/main.py` | XS | P2 |
| 7 | Implement safe mode logic | `core/safe_mode.py` | M | P2 |
| 8 | Add Prometheus pushgateway support (optional) | `core/metrics.py` | L | P3 |
| 9 | Write tests for metrics collection | `tests/test_metrics.py` | M | P1 |
| 10 | Document all metrics in `--help` | `cli/main.py` | XS | P3 |

### 13.2 Verification Commands

```bash
# Verify metrics collection
cd ~/Projects/recon
source .venv/bin/activate

# Run diagnostics
recon diagnostics --json

# Check log format
cat ~/.cache/recon/recon.log | head -5 | python -m json.tool

# Verify metrics file
recon search "solid state battery"
cat ~/.cache/recon/metrics.jsonl | tail -1 | python -m json.tool

# Run tests
pytest tests/test_metrics.py -xvs
```

---

## 14. Appendices

### Appendix A: Metric Naming Convention

All metrics follow Prometheus naming convention:
- `recon_<component>_<unit>` for gauges/counters
- `recon_<component>_duration_seconds` for timers
- `recon_<component>_total` for cumulative counters
- `recon_<component>_ratio` for ratios (0.0–1.0)
- Labels: `source`, `format`, `error_type`, `severity`

### Appendix B: Constitution Compliance

| Principle | Monitoring Compliance |
|-----------|----------------------|
| **Minimal dependencies** | `metrics.py` uses stdlib only; `psutil` optional |
| **Zero-AI default** | No ML-based anomaly detection; rule-based alerts only |
| **Transparency** | All metrics exposed via `--diagnostics`; JSONL logs |
| **Dry error voice** | Alerts use `ERR:` prefix; no stack traces in user output |
| **Speed over depth** | Metrics collected async, no blocking I/O |
| **Keyboard-first** | `recon diagnostics` is CLI command; no GUI required |

### Appendix C: External Resources

- [Google SRE Book — Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Textual Reactive Attributes](https://textual.textualize.io/guide/reactivity/)
- [Python logging cookbook](https://docs.python.org/3/howto/logging-cookbook.html)

---

*Document generated for RECON v0.2.0+ monitoring infrastructure. Review quarterly or after major release.*
*Last updated: 2026-06-22*
