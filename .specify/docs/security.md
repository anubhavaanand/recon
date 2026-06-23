# RECON Security & Access Control Document

## v1.0.0 | 2026-06-21

---

## 1. Document Metadata

| **Field** | **Value** |
|-----------|-----------|
| **Project** | RECON |
| **Version** | v1.0.0 |
| **Classification** | Internal |
| **Review Cycle** | Quarterly or after security incident |
| **Owner** | Project Maintainer |
| **Threat Model** | Local workstation compromise, API key exfiltration, supply chain attack |

---

## 2. System Context

### 2.1 Deployment Model

| **Attribute** | **Value** | **Security Implication** |
|---------------|-----------|--------------------------|
| **Deployment** | Self-hosted, single-workstation | No network attack surface; physical access is root access |
| **User Count** | 1 (local user) | No multi-user authentication required |
| **Network** | Outbound HTTPS only | No inbound ports; firewall not applicable |
| **Data Sensitivity** | API keys (USPTO, EPO, Lens.org) | Moderate — keys grant read access to patent databases |
| **No PII** | N/A | Patent data is public; no personal data handled |
| **No Payment Data** | N/A | No financial transactions |
| **No Health Data** | N/A | Not a HIPAA-covered entity |

### 2.2 Trust Boundaries

```
+---------------------------------------------------------------+
|              TRUST BOUNDARY: Workstation                       |
|  +-----------+    +-----------+    +-----------------------+  |
|  |  Terminal |--->|   RECON   |--->| ~/.config/recon/      |  |
|  |  (User)   |    |  (Python) |    | config.toml (0600)   |  |
|  +-----------+    +-----+-----+    +-----------------------+  |
|                         |                                     |
|                         v                                     |
|                  +-----------+                                |
|                  |  SQLite   |                                |
|                  |  (Local)  |                                |
|                  +-----+-----+                                |
|                         |                                     |
|                         v                                     |
|  +---------------------------------------------------------+ |
|  |         UNTRUSTED: External Patent APIs                  | |
|  |  USPTO (api.uspto.gov)       |  HTTPS + API Key        | |
|  |  EPO (ops.epo.org)           |  HTTPS + OAuth2          | |
|  |  WIPO (patentscope.wipo.int) |  HTTPS (no auth)         | |
|  |  Google Patents              |  HTTPS (unofficial)      | |
|  |  Lens.org (api.lens.org)     |  HTTPS + API Key        | |
|  +---------------------------------------------------------+ |
+---------------------------------------------------------------+
```

### 2.3 Key Security Principle

> **RECON is a local-first, single-user tool.** Security controls prioritize **data confidentiality** (API keys, search history) over **identity verification** (no users to authenticate). The primary threat is **local workstation compromise**, not remote exploitation.

---

## 3. Authentication Strategy

### 3.1 Decision: No User Authentication

| **Factor** | **Rationale** |
|------------|---------------|
| **Single-user tool** | No multi-user scenario; OS-level login is the authentication boundary |
| **Local execution** | Process runs with user's UID; no daemon or service |
| **No remote access** | No SSH, no web UI, no API server |
| **Constitution compliance** | Zero-AI default extends to zero identity management |

### 3.2 What Counts as "Authentication"

| **Layer** | **Mechanism** | **Responsibility** |
|-----------|---------------|-------------------|
| **OS Level** | Linux user login (password/PAM/YubiKey) | System administrator |
| **File System** | Unix permissions (0600 on config files) | RECON + OS |
| **API Level** | API keys + OAuth2 tokens | External providers (USPTO, EPO, etc.) |
| **Application** | None — runs as invoking user | N/A |

### 3.3 API Authentication Methods

| **API** | **Method** | **Storage** | **Lifetime** | **Rotation** | **Library** |
|---------|------------|-------------|--------------|--------------|-------------|
| **USPTO** | X-API-KEY header | ~/.config/recon/config.toml | Until revoked | Manual (USPTO portal) | httpx |
| **EPO** | OAuth2 Client Credentials | Same as above | Until revoked | Manual (EPO portal) | httpx + custom OAuth handler |
| **WIPO** | None | N/A | N/A | N/A | httpx |
| **Google Patents** | None | N/A | N/A | N/A | httpx |
| **Lens.org** | Authorization: Bearer | ~/.config/recon/config.toml | Until revoked | Manual (Lens portal) | httpx |

### 3.4 EPO OAuth2 Implementation

```python
# clients/base.py — EPO OAuth2 handler
class EPOAuthHandler:
    TOKEN_URL = "https://ops.epo.org/3.7/auth/accesstoken"

    def __init__(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self._token = None
        self._expires_at = 0.0

    async def get_token(self) -> str:
        if self._token and time.time() < self._expires_at - 300:
            return self._token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                auth=(self.consumer_key, self.consumer_secret),
                data={"grant_type": "client_credentials"}
            )
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            self._expires_at = time.time() + data["expires_in"]
            return self._token
```

### 3.5 No Session Management

| **What We Don't Have** | **Why** |
|------------------------|---------|
| JWT tokens | No stateful sessions; no web server |
| Session cookies | No browser; no HTTP server |
| Refresh tokens | EPO uses Client Credentials (no refresh token) |
| SSO/SAML/OIDC | Single user; overkill |

---

## 4. Authorization Strategy

### 4.1 Decision: No RBAC/ABAC/ACL

| **Model** | **Applicability** | **RECON Decision** |
|-----------|-------------------|-------------------|
| **RBAC** (Role-Based) | Multi-user systems with roles | Not applicable — single user |
| **ABAC** (Attribute-Based) | Fine-grained policy enforcement | Not applicable — no policies |
| **ACL** (Access Control List) | Resource-level permissions | Not applicable — all data is user's own |
| **Unix Permissions** | File-system level | Primary authorization mechanism |

### 4.2 Effective Authorization: Unix File Permissions

| **Resource** | **Owner** | **Group** | **Others** | **Enforcement** |
|--------------|-----------|-----------|------------|-----------------|
| ~/.config/recon/config.toml | rw------- (0600) | — | — | os.chmod(path, 0o600) on creation |
| ~/.cache/recon/ | rwx------ (0700) | — | — | os.mkdir(path, mode=0o700) |
| ~/Projects/recon/ | User's umask | — | — | Standard git permissions |
| SQLite DB (cache.db) | rw------- (0600) | — | — | Inherited from parent dir |

### 4.3 Permission Enforcement Code

```python
# core/config.py — Secure config file creation
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "recon"
CONFIG_FILE = CONFIG_DIR / "config.toml"

def ensure_secure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, 0o700)

def write_config(data: dict):
    ensure_secure_config_dir()
    temp_file = CONFIG_FILE.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        tomli_w.dump(data, f)
    os.chmod(temp_file, 0o600)
    os.replace(temp_file, CONFIG_FILE)
```

---

## 5. Role Definitions & Permission Matrix

### 5.1 Roles

RECON has **one implicit role: Local User**. The OS user is the sole actor.

### 5.2 Permission Matrix

| **Action** | **Local User** | **Other OS Users** | **External Process** | **Enforcement** |
|------------|----------------|-------------------|---------------------|-----------------|
| Read config (API keys) | Yes | No | No | 0600 file perms |
| Write config | Yes | No | No | 0600 file perms |
| Execute recon CLI | Yes | Yes* | No | PATH + exec perms |
| Read cache DB | Yes | No | No | 0700 dir perms |
| Write cache DB | Yes | No | No | 0700 dir perms |
| Export collections | Yes | No | No | 0700 dir perms |
| Access TUI | Yes | Yes* | No | Terminal ownership |
| Call external APIs | Yes | Yes* | No | Network egress |
| Modify source code | Yes | No | No | Git permissions |

*If installed system-wide via pip install. Recommended: pip install --user or virtualenv only.

### 5.3 Action-to-Permission Mapping

| **RECON Command** | **Files Touched** | **Network** | **Risk Level** |
|-------------------|-------------------|-------------|----------------|
| recon search | Cache DB (read/write) | HTTPS to APIs | Low |
| recon export | Cache DB (read), Export file (write) | None | Low |
| recon config set | Config file (write) | None | Medium (stores secrets) |
| recon config show | Config file (read) | None | Low |
| recon search (TUI) | Cache DB (read/write) | HTTPS to APIs | Low |

---

## 6. Secrets Management

### 6.1 Secret Inventory

| **Secret** | **Type** | **Storage** | **Lifetime** | **Rotation** |
|------------|----------|-------------|--------------|--------------|
| USPTO API Key | Bearer token | ~/.config/recon/config.toml | Until revoked | Manual (USPTO portal) |
| EPO Consumer Key | OAuth2 client_id | Same as above | Until revoked | Manual (EPO portal) |
| EPO Consumer Secret | OAuth2 client_secret | Same as above | Until revoked | Manual (EPO portal) |
| EPO Access Token | OAuth2 access_token | In-memory only (EPOAuthHandler._token) | 20 minutes | Automatic (auto-refresh) |
| Lens.org API Key | Bearer token | ~/.config/recon/config.toml | Until revoked | Manual (Lens portal) |

### 6.2 Storage Format

```toml
# ~/.config/recon/config.toml
# File permissions: 0600 (rw-------)

[api_keys]
uspto = "enc:AES256GCM:..."  # See Section 7 for encryption
epo_consumer_key = "enc:AES256GCM:..."
epo_consumer_secret = "enc:AES256GCM:..."
lens = "enc:AES256GCM:..."

[settings]
rate_limit_headroom = 0.24
default_sources = ["uspto", "wipo", "google_patents"]
```

### 6.3 No Environment Variables for Secrets

| **Approach** | **Status** | **Rationale** |
|--------------|------------|---------------|
| **Environment variables** | Rejected | Leaked via /proc/*/environ, shell history, ps |
| **Keyring / Secret Service** | Optional | Better security, but adds keyring dependency (violates minimal deps) |
| **File-based (0600)** | Chosen | Unix permissions are sufficient for single-user tool |
| **Hardcoded** | Rejected | Obvious security violation |

### 6.4 Rotation Policy

| **Trigger** | **Action** | **Responsible** |
|-------------|------------|-----------------|
| Key compromise suspected | Rotate immediately | User |
| Quarterly review | Verify keys still needed | User |
| API provider notification | Rotate per provider instructions | User |
| EPO token expiry | Auto-refresh (handled by EPOAuthHandler) | Application |

### 6.5 Rotation Procedure

```bash
# 1. Revoke old key at provider portal
# 2. Generate new key
# 3. Update RECON config
recon config set --uspto-key NEW_KEY_HERE

# 4. Verify old key no longer works
# 5. Delete old key from provider portal
```

---

## 7. Data Encryption

### 7.1 Encryption at Rest

| **Data** | **Method** | **Key** | **Status** |
|----------|------------|---------|------------|
| **Config file (API keys)** | AES-256-GCM via cryptography library | Derived from machine-specific secret | Recommended for v0.3.0 |
| **SQLite cache** | None (plaintext) | N/A | Acceptable — patent data is public |
| **Export files** | None | N/A | Acceptable — user controls destination |
| **Log files** | None | N/A | Acceptable — no sensitive data logged |

### 7.2 Config File Encryption (v0.3.0)

```python
# core/config.py — Optional encryption for API keys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class ConfigEncryption:
    def _derive_key(self):
        fingerprint = f"{os.uname().nodename}:{os.getlogin()}:{platform.machine()}"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"recon_v1_fixed_salt",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(fingerprint.encode()))

    def encrypt(self, plaintext: str) -> str:
        f = Fernet(self._derive_key())
        return f"enc:AES256GCM:{f.encrypt(plaintext.encode()).decode()}"

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext.startswith("enc:AES256GCM:"):
            return ciphertext
        f = Fernet(self._derive_key())
        token = ciphertext.replace("enc:AES256GCM:", "")
        return f.decrypt(token.encode()).decode()
```

**Constitutional Note:** cryptography is a heavy dependency. Consider pycryptodome or stdlib hashlib + secrets for lighter weight. For v0.2.0, plaintext with 0600 permissions is acceptable.

### 7.3 Encryption in Transit

| **Connection** | **Protocol** | **Verification** | **Library** |
|----------------|--------------|------------------|-------------|
| USPTO API | HTTPS (TLS 1.2+) | Certificate validation | httpx (default) |
| EPO API | HTTPS (TLS 1.2+) | Certificate validation | httpx (default) |
| WIPO API | HTTPS (TLS 1.2+) | Certificate validation | httpx (default) |
| Google Patents | HTTPS (TLS 1.2+) | Certificate validation | httpx (default) |
| Lens.org API | HTTPS (TLS 1.2+) | Certificate validation | httpx (default) |

### 7.4 TLS Configuration

```python
# clients/base.py — httpx client with strict TLS
import httpx

class SecureClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            http2=True,
            verify=True,  # STRICT: Never disable cert validation
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def request(self, method: str, url: str, **kwargs):
        if url.startswith("http://") and not url.startswith("http://localhost"):
            raise SecurityError("HTTP URLs rejected. Use HTTPS.")
        return await self.client.request(method, url, **kwargs)
```

### 7.5 No Certificate Pinning

| **Decision** | **Rationale** |
|--------------|---------------|
| No pinning | API providers rotate certificates; pinning breaks without warning |
| Standard CA validation | certifi bundle via httpx is sufficient |

---

## 8. Input Validation & Sanitization Rules

### 8.1 Search Query Validation

| **Input** | **Rule** | **Enforcement** | **Error Voice** |
|-----------|----------|-----------------|-----------------|
| **Query string** | Max 500 characters | Truncate or reject | ERR: Query exceeds 500 characters. |
| **Query string** | No null bytes | Strip or reject | ERR: Invalid characters in query. |
| **Query string** | No control characters | Strip | Silent sanitization |
| **Source list** | Must be subset of [uspto, epo, wipo, google_patents, lens] | Filter invalid | ERR: Unknown source: {source}. |
| **Limit** | Integer, 1-100 | Clamp to range | ERR: Limit must be 1-100. |

### 8.2 Config Value Validation

| **Input** | **Type** | **Validation** | **Error Voice** |
|-----------|----------|----------------|-----------------|
| **API key** | String | Min 8 chars, no whitespace | ERR: API key too short. |
| **Rate limit headroom** | Float | 0.0-0.95 | Clamp to range |
| **Cache TTL** | Integer | 1-365 days | Clamp to range |
| **Export format** | String | Must be in [csv, json, bibtex, markdown, pdf] | ERR: Unsupported format: {fmt}. |

### 8.3 Path Traversal Prevention

| **Operation** | **Rule** | **Enforcement** |
|---------------|----------|-----------------|
| **Export file path** | Must be within CWD or explicit --output-dir | Path.resolve() + prefix check |
| **Config path** | Fixed at ~/.config/recon/config.toml | Hardcoded |
| **Cache path** | Fixed at ~/.cache/recon/cache.db | Hardcoded |

```python
# cli/export.py — Path traversal prevention
def validate_export_path(path: Path) -> Path:
    resolved = path.resolve()
    cwd = Path.cwd().resolve()
    if not str(resolved).startswith(str(cwd)):
        raise SecurityError(f"ERR: Export path must be within {cwd}")
    return resolved
```

### 8.4 SQL Injection Prevention

| **Layer** | **Defense** | **Status** |
|-----------|-------------|------------|
| **Parameterized queries** | sqlite3 placeholders (?) | Always used |
| **String concatenation** | Never used for SQL | Prohibited |
| **User input in SQL** | Only query_hash (SHA256 hex) | Sanitized by design |

```python
# storage/cache.py — Safe query pattern
# CORRECT
cursor.execute(
    "SELECT * FROM search_results WHERE query_hash = ? AND expires_at > ?",
    (query_hash, now)
)

# INCORRECT — NEVER DO THIS
cursor.execute(f"SELECT * FROM search_results WHERE query_hash = '{user_input}'")
```

### 8.5 No Shell Injection

| **Operation** | **Rule** | **Enforcement** |
|---------------|----------|-----------------|
| **External viewer** | xdg-open with single file path | shlex.quote() wrapper |
| **Subprocess calls** | None in core; subprocess.run with list args only | Code review |

---

## 9. Rate Limiting & Brute Force Protection

### 9.1 External API Rate Limiting

| **API** | **Limit** | **RECON Headroom** | **Actual Rate** | **Implementation** |
|---------|-----------|-------------------|-----------------|-------------------|
| USPTO | 100/min | 24% | 76/min | TokenBucket in clients/base.py |
| EPO | 4/sec | 24% | 3.04/sec | TokenBucket |
| WIPO | 100/day | 24% | 76/day | TokenBucket |
| Google Patents | Unknown | Conservative: 10/min | 10/min | TokenBucket |
| Lens.org | 1000/day | 24% | 760/day | TokenBucket |

### 9.2 TokenBucket Implementation

```python
# clients/base.py
import asyncio
import time
from dataclasses import dataclass

@dataclass
class RateLimit:
    requests: int
    period: int

    def __post_init__(self):
        self.max_tokens = int(self.requests * 0.76)
        self.tokens = self.max_tokens
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * (self.max_tokens / self.period)
            )
            self.last_update = now

            if self.tokens < 1:
                wait = (1 - self.tokens) * (self.period / self.max_tokens)
                await asyncio.sleep(wait)
                self.tokens = 0

            self.tokens -= 1
```

### 9.3 No Brute Force Protection Needed

| **Reason** | **Explanation** |
|------------|-----------------|
| No login mechanism | No passwords to brute force |
| No web interface | No HTTP endpoints to attack |
| Local-only | Physical access = game over regardless |
| API keys are read-only | Even if stolen, attacker can only search patents |

### 9.4 Backoff Strategy

| **Scenario** | **Behavior** | **Implementation** |
|--------------|--------------|-------------------|
| HTTP 429 (Too Many Requests) | Exponential backoff: 1s -> 2s -> 4s -> 8s | get_with_backoff() in clients/base.py |
| HTTP 5xx | Same backoff, then fail | get_with_backoff() |
| Connection timeout | 1 retry, then fail | httpx timeout + manual retry |
| DNS failure | Immediate fail | No retry (transient) |

---

## 10. OWASP Top 10 (2021) — RECON Mapping

| **Rank** | **Risk** | **RECON Exposure** | **Mitigation** | **Status** |
|----------|----------|-------------------|----------------|------------|
| A01 | Broken Access Control | Low — single user | Unix permissions (0600/0700) | Mitigated |
| A02 | Cryptographic Failures | Low — API keys at rest | Optional AES-256-GCM (v0.3.0) | Acceptable risk |
| A03 | Injection | Low — SQLite, no web | Parameterized queries only | Mitigated |
| A04 | Insecure Design | Low — terminal tool | Constitution: minimal attack surface | Mitigated |
| A05 | Security Misconfiguration | Low — no server | Default secure: no open ports | Mitigated |
| A06 | Vulnerable Components | Medium — Python deps | pip-audit + safety scans | See Section 11 |
| A07 | Identification & Auth Failures | N/A — no auth | OS-level auth is boundary | N/A |
| A08 | Software & Data Integrity Failures | Medium — pip installs | Pin hashes in requirements | See Section 11 |
| A09 | Security Logging Failures | Low — no sensitive ops | Audit log to ~/.cache/recon/audit.log | Partial |
| A10 | Server-Side Request Forgery | N/A — no server | No SSRF vectors | N/A |

### 10.1 Specific OWASP Controls

#### A01: Broken Access Control
```python
# core/config.py — Permission enforcement
def ensure_secure_permissions(path: Path, mode: int = 0o600):
    os.chmod(path, mode)
    stat = path.stat()
    if stat.st_mode & 0o077:
        raise SecurityError(f"ERR: {path} has overly permissive permissions")
```

#### A03: Injection Prevention
```python
# storage/cache.py — Query builder (safe)
def search_cache(query_hash: str):
    cursor.execute(
        "SELECT data FROM search_results WHERE query_hash = ? AND expires_at > ?",
        (query_hash, time.time())
    )
    return [PatentRecord.from_json(row[0]) for row in cursor.fetchall()]
```

#### A06: Dependency Management
```bash
# Weekly scan (automated via cron or CI)
pip install pip-audit
pip-audit --requirement requirements.txt --format=json --output audit.json
```

---

## 11. Audit Logging

### 11.1 What to Log

| **Event** | **Level** | **Data Logged** | **Destination** |
|-----------|-----------|-----------------|-----------------|
| **Search executed** | INFO | Query hash, sources, result count, duration | ~/.cache/recon/audit.log |
| **API key used** | INFO | Provider (not the key itself), endpoint | Same |
| **Cache hit** | DEBUG | Query hash, age | Same |
| **Cache miss** | DEBUG | Query hash | Same |
| **Export performed** | INFO | Format, record count, destination path | Same |
| **Config changed** | WARNING | Key name (not value), timestamp | Same |
| **Rate limit hit** | WARNING | Provider, wait time | Same |
| **API error** | ERROR | Provider, HTTP status, error message | Same |
| **Security violation** | CRITICAL | Violation type, timestamp | Same + stderr |
| **Application start** | INFO | Version, Python version | Same |
| **Application exit** | INFO | Duration, searches performed | Same |

### 11.2 What NOT to Log

| **Data** | **Reason** | **Prevention** |
|----------|-----------|----------------|
| API keys | Credential exposure | Regex scrubber in logger formatter |
| Search queries (raw) | Privacy (queries may contain IP hints) | Hash or truncate |
| Patent record full text | Size | Log count only |
| User's OS username | Privacy | Exclude from logs |
| File paths outside project | Privacy | Truncate to basename |

### 11.3 Log Format

```python
# core/logging_config.py
import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "provider"):
            log_entry["provider"] = record.provider
        if hasattr(record, "query_hash"):
            log_entry["query_hash"] = record.query_hash
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        return json.dumps(log_entry)

logger = logging.getLogger("recon")
handler = logging.FileHandler(Path.home() / ".cache" / "recon" / "audit.log")
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### 11.4 Log Rotation

| **Policy** | **Value** | **Implementation** |
|------------|-----------|-------------------|
| **Max size** | 10 MB | logging.handlers.RotatingFileHandler |
| **Max backups** | 5 | Automatic |
| **Retention** | 90 days | Cron job or startup cleanup |

### 11.5 Audit Log Access

| **Action** | **Permitted** | **Enforcement** |
|------------|-------------|-----------------|
| Read audit log | Owner only | 0600 permissions |
| Delete audit log | Owner only | 0600 permissions |
| Modify audit log | Owner only | 0600 permissions (append-only recommended) |

---

## 12. Incident Response Brief

### 12.1 Incident Classification

| **Severity** | **Scenario** | **Example** |
|--------------|--------------|-------------|
| **Critical** | API key compromise | Key found in public repo, unauthorized usage detected |
| **High** | Local compromise | Workstation infected, potential key exfiltration |
| **Medium** | Dependency vulnerability | CVE in httpx or textual with remote exploit |
| **Low** | Information disclosure | Log file permissions too permissive (0644 instead of 0600) |

### 12.2 Response Playbook

#### API Key Compromise (Critical)

```
+---------------------------------------------------------------+
|  INCIDENT: API Key Compromise                                 |
+---------------------------------------------------------------+
|  1. REVOKE (0-5 min)                                          |
|     -> Log into USPTO/EPO/Lens portal                         |
|     -> Revoke compromised key immediately                     |
|     -> Document revocation timestamp                          |
|                                                                |
|  2. ROTATE (5-15 min)                                         |
|     -> Generate new key at provider portal                    |
|     -> Update RECON config: recon config set --provider-key NEW |
|     -> Verify old key returns 401/403                         |
|                                                                |
|  3. AUDIT (15-60 min)                                         |
|     -> Check ~/.cache/recon/audit.log for unauthorized usage  |
|     -> Review GitHub repo for accidental commits              |
|     -> Check shell history for key exposure                   |
|                                                                |
|  4. HARDEN (1-2 hours)                                        |
|     -> Enable config encryption (v0.3.0 feature)              |
|     -> Add .gitignore for config files                        |
|     -> Review file permissions (should be 0600)               |
|                                                                |
|  5. DOCUMENT (Ongoing)                                        |
|     -> Record incident in project notes                       |
|     -> Update rotation procedures if gap found                |
+---------------------------------------------------------------+
```

#### Local Workstation Compromise (High)

| **Step** | **Action** | **Time** |
|----------|------------|----------|
| 1. Isolate | Disconnect from network | Immediate |
| 2. Revoke | Rotate all API keys from clean device | 15 min |
| 3. Assess | Check ~/.cache/recon/ for exfiltration | 30 min |
| 4. Rebuild | Reinstall OS, restore from known-good backup | 4-8 hours |
| 5. Verify | Run recon config show on new install | 5 min |

#### Dependency Vulnerability (Medium)

| **Step** | **Action** | **Command** |
|----------|------------|-------------|
| 1. Detect | Run vulnerability scan | pip-audit --requirement requirements.txt |
| 2. Assess | Check CVSS score and exploitability | Review CVE details |
| 3. Patch | Update to fixed version | pip install --upgrade <package> |
| 4. Verify | Run full test suite | pytest -xvs |
| 5. Commit | Document update | git commit -m "security: patch CVE-XXXX-XXXX in <package>" |

### 12.3 Communication

| **Stakeholder** | **When to Notify** | **Method** |
|-------------------|-------------------|------------|
| Self (user) | All incidents | Terminal notification + log entry |
| API Providers | Key compromise | Provider support portal |
| GitHub (if repo affected) | Accidental secret commit | GitHub secret scanning |
| Community | CVE in dependency | GitHub Security Advisory |

### 12.4 Recovery Verification

```bash
# Post-incident verification checklist
cd ~/Projects/recon
source .venv/bin/activate

# 1. Verify no secrets in repo
git log --all --full-history -- . | grep -i "key\|secret\|token" || echo "Clean"

# 2. Verify config permissions
ls -la ~/.config/recon/config.toml  # Should show -rw-------

# 3. Verify cache permissions
ls -la ~/.cache/recon/  # Should show drwx------

# 4. Test API connectivity with new keys
recon search "test" --limit 1

# 5. Run full test suite
pytest -xvs

# 6. Verify audit log integrity
tail -50 ~/.cache/recon/audit.log | jq .
```

---

## 13. Dependency Vulnerability Management

### 13.1 Dependency Inventory

| **Package** | **Version** | **Purpose** | **Risk Level** | **Update Frequency** |
|-------------|-------------|-------------|----------------|----------------------|
| textual | ^0.x | TUI framework | Medium | Monthly |
| httpx | ^0.x | HTTP client | Medium | Monthly |
| Pillow | ^10.x | Image processing | Low | Quarterly |
| rapidfuzz | ^3.x | Fuzzy matching | Low | Quarterly |
| typer | ^0.x | CLI framework | Low | Quarterly |
| fpdf2 | ^2.x | PDF generation | Low | Quarterly |
| tomli | ^2.x | TOML parsing (Python < 3.11) | Low | Quarterly |
| tomli-w | ^1.x | TOML writing | Low | Quarterly |

### 13.2 Scanning Tools

| **Tool** | **Command** | **Output** | **Frequency** |
|----------|-------------|------------|---------------|
| **pip-audit** | pip-audit -r requirements.txt | JSON/CLI | Weekly |
| **safety** | safety check | CLI table | Weekly |
| **dependabot** | GitHub native | PRs | Continuous |
| **snyk** | snyk test | Web UI + CLI | Monthly |

### 13.3 CI/CD Integration

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install pip-audit
          pip install -r requirements.txt

      - name: Run pip-audit
        run: pip-audit --requirement requirements.txt --format=json --output=audit.json

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: audit-results
          path: audit.json
```

### 13.4 Pinned Dependencies

```txt
# requirements.txt — Pinned with hashes (generated via pip-compile)
textual==0.52.1 \
    --hash=sha256:abc123...
httpx==0.27.0 \
    --hash=sha256:def456...
# ... etc
```

### 13.5 Update Policy

| **Severity** | **Response Time** | **Action** |
|--------------|-------------------|------------|
| Critical (CVSS 9.0+) | 24 hours | Emergency patch release |
| High (CVSS 7.0-8.9) | 7 days | Scheduled patch |
| Medium (CVSS 4.0-6.9) | 30 days | Next minor release |
| Low (CVSS 0.1-3.9) | 90 days | Next major release or defer |

---

## 14. Security Checklist

### 14.1 Pre-Release Checklist

| **#** | **Check** | **Verification** | **Status** |
|-------|-----------|------------------|------------|
| 1 | Config file permissions are 0600 | ls -la ~/.config/recon/config.toml | Unchecked |
| 2 | Cache directory permissions are 0700 | ls -la ~/.cache/recon/ | Unchecked |
| 3 | No secrets in git history | git log --all -S 'api_key' | Unchecked |
| 4 | No secrets in source code | grep -rn 'sk-\|api_key\|secret' --include='*.py' . | Unchecked |
| 5 | All SQL queries parameterized | grep -rn 'execute(' --include='*.py' . | Unchecked |
| 6 | No HTTP URLs in production code | grep -rn 'http://' --include='*.py' . | Unchecked |
| 7 | TLS verification enabled | grep -rn 'verify=False' --include='*.py' . | Unchecked |
| 8 | Rate limiting implemented | Check clients/base.py for TokenBucket | Unchecked |
| 9 | Audit logging configured | Check ~/.cache/recon/audit.log exists | Unchecked |
| 10 | Dependency scan clean | pip-audit returns 0 vulnerabilities | Unchecked |
| 11 | Tests pass | pytest -xvs all green | Unchecked |
| 12 | Error voice uses ERR: prefix | grep -rn 'print(' --include='*.py' . | Unchecked |

### 14.2 Quarterly Review Checklist

| **#** | **Check** | **Action** |
|-------|-----------|------------|
| 1 | Rotate API keys | Generate new keys, update config |
| 2 | Review audit logs | Check for anomalies |
| 3 | Update dependencies | pip list --outdated |
| 4 | Run vulnerability scan | pip-audit + safety |
| 5 | Verify file permissions | find ~/.config/recon ~/.cache/recon -type f -perm /o+rwx |
| 6 | Check GitHub repo for leaked secrets | GitHub secret scanning alerts |
| 7 | Review access logs (if any) | Check ~/.cache/recon/audit.log |
| 8 | Update incident response contacts | Verify provider portal access |

---

## 15. Appendices

### Appendix A: Security-Related Code Patterns

#### A.1 Secure File Creation

```python
import os
import tempfile
from pathlib import Path

def secure_write(path: Path, content: str, mode: int = 0o600):
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp")
    try:
        os.write(fd, content.encode())
        os.fchmod(fd, mode)
        os.close(fd)
        os.replace(temp_path, path)
    except Exception:
        os.close(fd)
        os.unlink(temp_path)
        raise
```

#### A.2 Secure Random Generation

```python
import secrets

def generate_nonce(length: int = 16) -> str:
    return secrets.token_hex(length)
```

#### A.3 Input Sanitization

```python
import re

def sanitize_query(query: str) -> str:
    query = query.replace(' ', '')
    query = re.sub(r'[-]', '', query)
    return query[:500]
```

### Appendix B: External Resources

| **Resource** | **URL** | **Purpose** |
|--------------|---------|-------------|
| USPTO API Docs | https://developer.uspto.gov/api-catalog | API key management |
| EPO Developer Portal | https://developers.epo.org/ | OAuth2 setup |
| WIPO PATENTSCOPE | https://www.wipo.int/patentscope/ | API docs |
| Lens.org API | https://www.lens.org/lens/user/subscriptions | API access |
| pip-audit | https://github.com/pypa/pip-audit | Dependency scanning |
| Python Security | https://security.python.org/ | PSIRT advisories |
| OWASP Top 10 | https://owasp.org/Top10/ | General reference |

### Appendix C: Glossary

| **Term** | **Definition** |
|----------|----------------|
| **API Key** | Secret token for authenticating to external APIs |
| **AES-256-GCM** | Advanced Encryption Standard with 256-bit key, Galois/Counter Mode |
| **OAuth2** | Authorization framework for delegated access |
| **Token Bucket** | Rate limiting algorithm allowing burst traffic |
| **TLS** | Transport Layer Security (HTTPS) |
| **CVSS** | Common Vulnerability Scoring System |
| **0600** | Unix permission: owner read/write only |
| **PBKDF2** | Password-Based Key Derivation Function 2 |

---

*Document Version: 1.0.0*
*Last Updated: 2026-06-21*
*Next Review: 2026-09-21*
