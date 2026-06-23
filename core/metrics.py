import logging
import json
import os
import time
from dataclasses import dataclass, asdict
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, List
from enum import Enum

SESSION_ID = ""
VERSION = "0.2.0"


class Severity(Enum):
    P0 = "critical"
    P1 = "high"
    P2 = "medium"
    P3 = "low"


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
        extra = getattr(record, "extra", None)
        if extra:
            log_obj.update(extra)
        return json.dumps(log_obj)


def setup_logging(debug: bool = False) -> logging.Logger:
    log_dir = os.path.expanduser("~/.cache/recon")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "recon.debug.log" if debug else "recon.log")
    max_bytes = 50 * 1024 * 1024 if debug else 10 * 1024 * 1024
    backup_count = 3 if debug else 5

    logger = logging.getLogger("recon")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setFormatter(JSONFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


_logger = setup_logging()


def log_event(
    level: str,
    component: str,
    event: str,
    message: str = "",
    extra: Optional[dict] = None,
) -> None:
    log_fn = getattr(_logger, level.lower(), _logger.info)
    log_fn(message, extra={"component": component, "event": event, **(extra or {})})


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

    def record_api_call(
        self, source: str, success: bool, rate_limit_used: float = 0.0
    ):
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
            src: data["rate_limit_max"] for src, data in self.api_calls.items()
        }

        alerts = self._evaluate_alerts(cache_ratio, api_error_rate, rate_limits)

        return MetricSnapshot(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            session_id=self.session_id,
            version=self.version,
            search_latency_ms=(
                sum(self.latencies[-10:]) / min(len(self.latencies), 10)
                if self.latencies
                else 0
            ),
            cache_hit_ratio=cache_ratio,
            memory_mb=self.get_memory_mb(),
            api_error_rate=api_error_rate,
            rate_limit_proximity=rate_limits,
            active_alerts=alerts,
        )

    def _evaluate_alerts(
        self, cache_ratio: float, api_error_rate: float, rate_limits: Dict[str, float]
    ) -> List[Dict]:
        alerts = []

        if api_error_rate > 0.05:
            alerts.append(
                {
                    "metric": "recon_api_error_rate",
                    "value": api_error_rate,
                    "threshold": 0.05,
                    "severity": Severity.P0.value,
                    "runbook": "RB-002",
                }
            )

        for source, proximity in rate_limits.items():
            if proximity > 0.76:
                alerts.append(
                    {
                        "metric": "recon_rate_limit_proximity",
                        "source": source,
                        "value": proximity,
                        "threshold": 0.76,
                        "severity": Severity.P1.value,
                        "runbook": "RB-003",
                    }
                )

        if cache_ratio < 0.5 and (self.cache_hits + self.cache_misses) > 10:
            alerts.append(
                {
                    "metric": "recon_cache_hit_ratio",
                    "value": cache_ratio,
                    "threshold": 0.5,
                    "severity": Severity.P2.value,
                    "runbook": "RB-008",
                }
            )

        return alerts

    def write_snapshot(self, path: str = "~/.cache/recon/metrics.jsonl"):
        snap = self.snapshot()
        expanded = os.path.expanduser(path)
        os.makedirs(os.path.dirname(expanded), exist_ok=True)
        with open(expanded, "a") as f:
            f.write(json.dumps(asdict(snap)) + "\n")
