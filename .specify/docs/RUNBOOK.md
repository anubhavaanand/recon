# RECON Operations Runbook

> **Status:** Production | **On-Call:** You | **Last Updated:** 2026-06-22
>
> **If this is an emergency:** Skip to [Section 11: Emergency Shutdown](#11-emergency-shutdown).

---

## System Overview

| Component | Value |
|---|---|
| **Project** | RECON — Terminal-native patent research tool |
| **Infra** | Single-process local Python application (no server, no Docker, no K8s) |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) |
| **Database** | SQLite (`~/.local/share/recon/cache.db`) |
| **Process Manager** | N/A — user-launched CLI/TUI process |
| **Python Version** | 3.12+ |
| **Entry Point** | `recon` (installed via `pip install -e .`) |
| **Config** | `~/.config/recon/config.toml` |
| **Logs** | `~/.local/share/recon/logs/recon.log` |
| **Repo** | `https://github.com/anubhavaanand/recon` |

**Architecture:** Single-process monolith. User runs `recon search` (TUI) or `recon search "query"` (CLI table). No background daemon. No network service. No horizontal scaling.

---

## 1. Initial Deployment (Zero to Live)

**Prerequisites:** Python 3.12+, `git`, `pip`, terminal with Unicode support.

### 1.1 Clone Repository

```bash
cd ~/Projects
git clone https://github.com/anubhavaanand/recon.git
cd recon
```

### 1.2 Create Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 1.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

### 1.4 Verify Installation

```bash
recon --version
recon --help
```

**Expected output:**
```
Usage: recon [OPTIONS] COMMAND [ARGS]...

Commands:
  search   Launch patent search (TUI or CLI table)
  export   Export collection to file
  config   Manage API keys and settings
```

### 1.5 Create Config Directory

```bash
mkdir -p ~/.config/recon
mkdir -p ~/.local/share/recon/logs
chmod 700 ~/.config/recon
chmod 700 ~/.local/share/recon
```

### 1.6 Set API Keys (Required for Live Search)

```bash
# USPTO (get key at https://developer.uspto.gov/)
recon config set --uspto-key YOUR_USPTO_KEY

# EPO (get credentials at https://developers.epo.org/)
recon config set --epo-consumer-key YOUR_EPO_KEY
recon config set --epo-consumer-secret YOUR_EPO_SECRET

# Verify
recon config show
```

### 1.7 Run Smoke Test

```bash
# Test with mock data (no keys needed)
recon search "solid state battery"

# Expected: rich table with 3 mock patents
```

### 1.8 Verify File Permissions

```bash
ls -la ~/.config/recon/config.toml
# Expected: -rw------- (0600)

chmod 600 ~/.config/recon/config.toml
```

---

## 2. Routine Deployment (Update Existing Installation)

### 2.1 Pull Latest Code

```bash
cd ~/Projects/recon
git pull origin main
```

### 2.2 Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 2.3 Reinstall Package

```bash
pip install -e . --force-reinstall --no-deps
```

### 2.4 Run Full Test Suite

```bash
pytest -xvs
```

**Expected:** `37 passed` in under 5 seconds.

### 2.5 Verify CLI Commands

```bash
recon --help
recon search --help
recon export --help
recon config --help
```

### 2.6 Test Live Search (if keys configured)

```bash
recon search "semiconductor packaging"
```

### 2.7 If Tests Fail — Stop Here

```bash
# Do NOT deploy. Check:
git log --oneline -5
pytest -xvs --tb=long
```

**Escalate to:** Check GitHub Issues for known regressions.

---

## 3. Rollback Procedure

### 3.1 Identify Last Known Good Version

```bash
cd ~/Projects/recon
git log --oneline -10
```

### 3.2 Rollback to Previous Commit

```bash
# Soft rollback (keep changes as unstaged)
git reset --soft HEAD~1

# Hard rollback (discard all changes)
git reset --hard HEAD~1

# Or rollback to specific commit
git reset --hard COMMIT_HASH
```

### 3.3 Reinstall After Rollback

```bash
source .venv/bin/activate
pip install -e . --force-reinstall --no-deps
```

### 3.4 Verify Rollback

```bash
pytest -xvs
recon search "test"
```

### 3.5 Rollback Config (If Corrupted)

```bash
# Backup current config
cp ~/.config/recon/config.toml ~/.config/recon/config.toml.bak.$(date +%s)

# Restore from last known good
cp ~/.config/recon/config.toml.bak.LAST_TIMESTAMP ~/.config/recon/config.toml
chmod 600 ~/.config/recon/config.toml
```

### 3.6 Rollback Database (If Corrupted)

```bash
# Backup current DB
cp ~/.local/share/recon/cache.db ~/.local/share/recon/cache.db.bak.$(date +%s)

# Restore from last known good
cp ~/.local/share/recon/cache.db.bak.LAST_TIMESTAMP ~/.local/share/recon/cache.db
```

---

## 4. Service Restart

**RECON has no background service.** It is a user-launched CLI process. However, if you need to "restart" after config changes:

### 4.1 After Config Change

```bash
# No restart needed — config is read on every invocation
recon config show
```

### 4.2 After Code Update

```bash
cd ~/Projects/recon
source .venv/bin/activate
pip install -e . --force-reinstall --no-deps
```

### 4.3 Clear Cache (If Stale Data)

```bash
rm ~/.local/share/recon/cache.db
# Or use SQLite:
sqlite3 ~/.local/share/recon/cache.db "DELETE FROM search_results;"
```

### 4.4 Kill Hung TUI Process

```bash
# Find process
ps aux | grep "recon search" | grep -v grep

# Kill specific PID
kill -9 PID

# Or kill all recon processes
pkill -f "recon search"
```

---

## 5. Database Backup

### 5.1 Automated Daily Backup (Cron)

```bash
# Add to crontab
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * cp ~/.local/share/recon/cache.db ~/.local/share/recon/backups/cache.db.$(date +'%Y%m%d')

# Create backup directory
mkdir -p ~/.local/share/recon/backups
```

### 5.2 Manual Backup

```bash
# Timestamped backup
cp ~/.local/share/recon/cache.db ~/.local/share/recon/cache.db.bak.$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -lh ~/.local/share/recon/cache.db.bak.*
```

### 5.3 Backup Config

```bash
cp ~/.config/recon/config.toml ~/.config/recon/config.toml.bak.$(date +%Y%m%d_%H%M%S)
```

### 5.4 Export Collections as JSON (Portable Backup)

```bash
recon export --format json --output collection_backup_$(date +%Y%m%d).json
```

---

## 6. Database Restore

### 6.1 From SQLite Backup

```bash
# Stop any running recon processes
pkill -f "recon search"

# Backup current (possibly corrupted) DB
cp ~/.local/share/recon/cache.db ~/.local/share/recon/cache.db.corrupt.$(date +%s)

# Restore from backup
cp ~/.local/share/recon/cache.db.bak.TIMESTAMP ~/.local/share/recon/cache.db

# Verify
sqlite3 ~/.local/share/recon/cache.db ".tables"
```

### 6.2 From JSON Export

```bash
# If you have a JSON export, re-import via Python
python3 << 'EOF'
import json, sqlite3, os
from datetime import datetime

db_path = os.path.expanduser("~/.local/share/recon/cache.db")
json_path = "collection_backup_YYYYMMDD.json"

with open(json_path) as f:
    data = json.load(f)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for record in data:
    cursor.execute('''
        INSERT OR REPLACE INTO collections 
        (patent_id, title, data, created_at) 
        VALUES (?, ?, ?, ?)
    ''', (
        record['id'],
        record['title'],
        json.dumps(record),
        datetime.now().isoformat()
    ))

conn.commit()
conn.close()
print(f"Restored {len(data)} records")
EOF
```

### 6.3 Complete Reset (Nuclear Option)

```bash
# Backup everything first
cp -r ~/.local/share/recon ~/.local/share/recon.fullbak.$(date +%s)
cp -r ~/.config/recon ~/.config/recon.fullbak.$(date +%s)

# Delete and reinitialize
rm ~/.local/share/recon/cache.db
recon search "test"  # This will recreate the DB
```

---

## 7. Secrets Rotation

### 7.1 Rotate USPTO API Key

```bash
# 1. Get new key from https://developer.uspto.gov/
# 2. Update config
recon config set --uspto-key NEW_KEY

# 3. Verify
recon config show | grep USPTO

# 4. Test live search
recon search "battery"

# 5. Securely delete old key from clipboard
# (depends on your terminal — usually just copy something else)
```

### 7.2 Rotate EPO Credentials

```bash
# 1. Get new credentials from https://developers.epo.org/
recon config set --epo-consumer-key NEW_KEY
recon config set --epo-consumer-secret NEW_SECRET

# 2. Verify
recon config show | grep EPO

# 3. Test
recon search "semiconductor"
```

### 7.3 Verify Config File Permissions After Rotation

```bash
ls -la ~/.config/recon/config.toml
# Must show: -rw------- (0600)

chmod 600 ~/.config/recon/config.toml
```

### 7.4 Audit Config for Stale Keys

```bash
# Check file modification time
stat ~/.config/recon/config.toml

# List backup configs (may contain old keys)
ls -la ~/.config/recon/config.toml.bak.*

# Securely delete old backups
shred -u ~/.config/recon/config.toml.bak.*
```

---

## 8. Checking Logs

### 8.1 Log File Location

```bash
cat ~/.local/share/recon/logs/recon.log
```

### 8.2 Follow Logs in Real-Time

```bash
tail -f ~/.local/share/recon/logs/recon.log
```

### 8.3 Filter for Errors Only

```bash
grep "ERR:" ~/.local/share/recon/logs/recon.log
```

### 8.4 Filter for API Calls

```bash
grep "API" ~/.local/share/recon/logs/recon.log
```

### 8.5 Filter for Specific Time Range

```bash
# Last hour
grep "$(date '+%Y-%m-%d %H:')" ~/.local/share/recon/logs/recon.log

# Specific date
grep "2026-06-22" ~/.local/share/recon/logs/recon.log
```

### 8.6 Filter for Rate Limit Events

```bash
grep -i "rate.limit\|429\|backoff" ~/.local/share/recon/logs/recon.log
```

### 8.7 Filter for Cache Operations

```bash
grep -i "cache\|sqlite" ~/.local/share/recon/logs/recon.log
```

### 8.8 View Last 50 Lines

```bash
tail -n 50 ~/.local/share/recon/logs/recon.log
```

### 8.9 Export Logs for Analysis

```bash
cp ~/.local/share/recon/logs/recon.log /tmp/recon_logs_$(date +%Y%m%d).txt
```

### 8.10 If Log File is Missing

```bash
# Recreate log directory
mkdir -p ~/.local/share/recon/logs

# Test logging
python3 -c "import logging; logging.basicConfig(filename='~/.local/share/recon/logs/recon.log', level=logging.INFO); logging.info('Test log entry')"
```

---

## 9. Health Check

### 9.1 Quick Health Check (30 seconds)

```bash
cd ~/Projects/recon
source .venv/bin/activate

# 1. Version check
recon --version

# 2. Help check
recon --help > /dev/null && echo "CLI OK"

# 3. Config check
recon config show > /dev/null && echo "Config OK"

# 4. Mock search check
recon search "test" > /dev/null && echo "Search OK"

# 5. Test suite
pytest -x --tb=short > /dev/null && echo "Tests OK"

echo "All health checks passed"
```

### 9.2 Detailed Health Check

```bash
# Check Python version
python3 --version | grep "3.12"

# Check virtual environment
which python3 | grep ".venv"

# Check installed packages
pip list | grep -E "textual|httpx|Pillow|rapidfuzz|typer|fpdf2"

# Check database exists and is readable
sqlite3 ~/.local/share/recon/cache.db "SELECT COUNT(*) FROM search_results;"

# Check config file permissions
stat -c "%a" ~/.config/recon/config.toml | grep "600"

# Check disk space for cache
df -h ~/.local/share/recon/

# Check log file size
ls -lh ~/.local/share/recon/logs/recon.log
```

### 9.3 API Health Check (if keys configured)

```bash
# USPTO
recon search "US1234567" --source uspto

# WIPO
recon search "WO2024000001" --source wipo

# Check for ERR: in output
recon search "test" 2>&1 | grep "ERR:" && echo "API ERRORS FOUND" || echo "No API errors"
```

### 9.4 TUI Health Check

```bash
# Launch TUI, wait 2 seconds, send 'q' to quit
timeout 5 bash -c 'echo "q" | recon search'

# Exit code 0 = TUI launched and quit successfully
# Exit code 124 = TUI hung (timeout)
```

---

## 10. Scaling Up

**RECON does not scale horizontally.** It is a single-user, single-process CLI tool. However, you can scale vertically and optimize performance.

### 10.1 Vertical Scaling (Single Machine)

```bash
# Check current resource usage
ps aux | grep "recon"
top -p $(pgrep -f "recon search")

# Increase SQLite cache size
sqlite3 ~/.local/share/recon/cache.db "PRAGMA cache_size = 10000;"

# Enable WAL mode for better concurrency
sqlite3 ~/.local/share/recon/cache.db "PRAGMA journal_mode = WAL;"
```

### 10.2 Optimize Cache Performance

```bash
# Vacuum database to reclaim space
sqlite3 ~/.local/share/recon/cache.db "VACUUM;"

# Analyze for query optimization
sqlite3 ~/.local/share/recon/cache.db "ANALYZE;"

# Check database size
ls -lh ~/.local/share/recon/cache.db
```

### 10.3 Parallel Searches (Multiple Terminals)

```bash
# Terminal 1
recon search "battery"

# Terminal 2
recon search "solar"

# Each process is independent — no shared state conflicts
```

### 10.4 What You CANNOT Do

```bash
# ❌ Do NOT run as a systemd service (no daemon mode)
# ❌ Do NOT run in Docker (violates constitution: minimal deps)
# ❌ Do NOT run behind a load balancer (single-user tool)
# ❌ Do NOT share cache.db between users (file locking issues)
```

### 10.5 If Cache Grows Too Large

```bash
# Check current size
ls -lh ~/.local/share/recon/cache.db

# Purge old cache entries (older than 30 days)
sqlite3 ~/.local/share/recon/cache.db "DELETE FROM search_results WHERE cached_at < datetime('now', '-30 days');"

# Or full reset
rm ~/.local/share/recon/cache.db
```

---

## 11. Emergency Shutdown

### 11.1 Scenario: Hung TUI Process

```bash
# Find the process
ps aux | grep "recon search" | grep -v grep

# Kill it
kill -9 $(pgrep -f "recon search")

# Verify it's gone
ps aux | grep "recon" | grep -v grep
```

### 11.2 Scenario: Runaway API Calls (Rate Limit Storm)

```bash
# Kill all recon processes
pkill -9 -f "recon"

# Check logs for rate limit errors
tail -n 100 ~/.local/share/recon/logs/recon.log | grep "429"

# Wait 60 seconds for rate limits to reset
sleep 60

# Test with minimal query
recon search "test"
```

### 11.3 Scenario: Corrupted Database

```bash
# Stop any running recon
pkill -f "recon"

# Backup corrupted DB
cp ~/.local/share/recon/cache.db ~/.local/share/recon/cache.db.emergency.$(date +%s)

# Restore from last good backup
LATEST_BACKUP=$(ls -t ~/.local/share/recon/cache.db.bak.* | head -1)
cp "$LATEST_BACKUP" ~/.local/share/recon/cache.db

# If no backup exists, delete and recreate
rm ~/.local/share/recon/cache.db
recon search "test"
```

### 11.4 Scenario: API Key Compromise

```bash
# 1. Kill all recon processes
pkill -9 -f "recon"

# 2. Revoke keys at provider portals
# USPTO: https://developer.uspto.gov/ → My Apps → Revoke
# EPO: https://developers.epo.org/ → Revoke

# 3. Delete local config
rm ~/.config/recon/config.toml

# 4. Generate new keys at provider portals

# 5. Reconfigure
recon config set --uspto-key NEW_KEY
recon config set --epo-consumer-key NEW_KEY
recon config set --epo-consumer-secret NEW_SECRET

# 6. Test
recon search "test"
```

### 11.5 Scenario: Complete System Compromise

```bash
# 1. Kill all processes
pkill -9 -f "recon"

# 2. Securely delete all data
shred -u ~/.config/recon/config.toml
shred -u ~/.local/share/recon/cache.db
rm -rf ~/.local/share/recon/logs/

# 3. Remove installation
cd ~/Projects/recon
rm -rf .venv/
rm -rf __pycache__/
rm -rf *.egg-info/

# 4. Reclone and reinstall
cd ~
rm -rf ~/Projects/recon
git clone https://github.com/anubhavaanand/recon.git
cd recon
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .

# 5. Generate new keys and reconfigure
# (see Section 7)
```

### 11.6 Post-Emergency Verification

```bash
# Run full health check (Section 9)
pytest -xvs
recon config show
recon search "test"

# Check no ERR: in logs
grep "ERR:" ~/.local/share/recon/logs/recon.log | tail -n 5
```

---

## Quick Reference Card

| Task | Command |
|---|---|
| **Install** | `pip install -e .` |
| **Test** | `pytest -xvs` |
| **Search** | `recon search "query"` |
| **TUI** | `recon search` |
| **Export** | `recon export --format json` |
| **Config** | `recon config show` |
| **Logs** | `tail -f ~/.local/share/recon/logs/recon.log` |
| **Errors** | `grep "ERR:" ~/.local/share/recon/logs/recon.log` |
| **Backup DB** | `cp ~/.local/share/recon/cache.db ~/.local/share/recon/cache.db.bak.$(date +%Y%m%d)` |
| **Restore DB** | `cp ~/.local/share/recon/cache.db.bak.TIMESTAMP ~/.local/share/recon/cache.db` |
| **Kill hung** | `pkill -9 -f "recon search"` |
| **Clear cache** | `rm ~/.local/share/recon/cache.db` |
| **Check perms** | `ls -la ~/.config/recon/config.toml` |
| **Health** | `recon --version && pytest -x --tb=short` |

---

## Escalation

| Issue | Action |
|---|---|
| Test failures after deployment | `git reset --hard HEAD~1 && pip install -e .` |
| API key errors | Rotate keys (Section 7), check provider status pages |
| Database corruption | Restore from backup (Section 6), or `rm` and recreate |
| TUI crashes | Check `tui/screens.py` for `highlighted_child` usage |
| Rate limit storms | Wait 60s, check logs for 429 errors |
| Unknown error | `grep "ERR:" ~/.local/share/recon/logs/recon.log` |

**If all else fails:** `rm -rf ~/.local/share/recon/cache.db && recon search "test"`

---

*End of Runbook. Keep this file in `~/Projects/recon/docs/RUNBOOK.md`.*
