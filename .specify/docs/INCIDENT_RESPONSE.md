# RECON Incident Response Document

> **Classification:** Internal | **Owner:** Solo Maintainer | **Last Review:** 2026-06-22
>
> **Scope:** This document covers incident response for RECON, a terminal-native, single-user CLI/TUI patent research tool. Incidents are primarily local-machine issues (data loss, API key compromise, corrupted cache) rather than service outages.
>
> **On-Call:** You are the sole maintainer and responder. There is no escalation chain beyond this document.

---

## Table of Contents

1. [Severity Level Definitions](#1-severity-level-definitions)
2. [Incident Detection](#2-incident-detection)
3. [Incident Response Checklist](#3-incident-response-checklist)
4. [Escalation Matrix](#4-escalation-matrix)
5. [Communication Templates](#5-communication-templates)
6. [War Room Protocol](#6-war-room-protocol)
7. [Postmortem Template](#7-postmortem-template)
8. [Blameless Culture Guidelines](#8-blameless-culture-guidelines)
9. [Common Incident Playbooks](#9-common-incident-playbooks)
10. [Post-Incident Review Process](#10-post-incident-review-process)

---

## 1. Severity Level Definitions

| Severity | Name | Response Time SLA | Resolution Target | Examples |
|---|---|---|---|---|
| **P0 — Critical** | Data Loss / Security Breach | Immediate (< 15 min) | < 4 hours | Corrupted cache with no backup; API keys leaked in public repo; `~/.config/recon/config.toml` has `0644` permissions; malware detected in dependency |
| **P1 — High** | Core Functionality Broken | < 1 hour | < 24 hours | `recon search` crashes on launch; all API calls return `ERR:`; TUI completely unresponsive; tests fail after `git pull`; export produces corrupt files |
| **P2 — Medium** | Partial Degradation | < 4 hours | < 72 hours | One API source (USPTO) down, others work; TUI preview tabs empty but CLI works; slow search (> 10s); cache not expiring after 30 days |
| **P3 — Low** | Cosmetic / Minor | < 24 hours | Next release | Typos in help text; color scheme off in specific terminal; keyboard shortcut conflict; missing log entry |

### Severity Determination Flowchart

```
Is user data at risk or exposed?
  ├─ YES → P0
  └─ NO → Is the tool completely unusable?
      ├─ YES → P1
      └─ NO → Is a major feature degraded?
          ├─ YES → P2
          └─ NO → P3
```

### Severity-Specific Response Actions

| Severity | Immediate Action | Do NOT Do |
|---|---|---|
| **P0** | Stop all work. Isolate machine from network if keys leaked. | Continue using tool; delay key rotation |
| **P1** | `git stash` current work. Rollback to last known good commit. | Run `git pull` again; edit code while stressed |
| **P2** | Document workaround in `KNOWN_ISSUES.md`. Continue with degraded mode. | Ignore — will worsen over time |
| **P3** | Add to backlog. Fix during next polish session. | Escalate; waste time on non-critical |

---

## 2. Incident Detection

### 2.1 Detection Channels

| Channel | Method | Frequency | Owner |
|---|---|---|---|
| **Test Suite Failure** | `pytest -xvs` fails after code change | On every `git pull` or edit | User |
| **CLI Error Output** | `ERR:` prefix in terminal | Every invocation | User |
| **Log Monitoring** | `tail -f ~/.local/share/recon/logs/recon.log` | During active debugging | User |
| **User Report** | GitHub Issue or direct message | Ad-hoc | Community (if any) |
| **API Provider Alert** | USPTO/EPO rate limit email | Ad-hoc | User (registered email) |
| **Dependency CVE** | `pip-audit` or `safety` scan | Weekly (automated via cron) | User |
| **File Integrity** | `ls -la ~/.config/recon/config.toml` | On suspicion | User |

### 2.2 Automated Detection Setup

```bash
# Add to crontab for weekly dependency CVE scan
crontab -e

# Weekly pip-audit (Sundays at 3 AM)
0 3 * * 0 cd ~/Projects/recon && source .venv/bin/activate && pip-audit --format=json > /tmp/pip_audit_$(date +'%Y%m%d').json 2>&1 || echo "CVEs found" | mail -s "RECON Dependency Alert" your-email@example.com

# Daily log size check (alerts if > 100MB)
0 4 * * * if [ $(stat -c%s ~/.local/share/recon/logs/recon.log 2>/dev/null || echo 0) -gt 104857600 ]; then echo "RECON log file > 100MB" | mail -s "RECON Log Alert" your-email@example.com; fi
```

### 2.3 Manual Detection Commands

```bash
# Quick health check (run this if anything feels wrong)
cd ~/Projects/recon && source .venv/bin/activate && pytest -x --tb=short && recon --version && echo "HEALTHY" || echo "INCIDENT DETECTED"

# Check for errors in last 24 hours
grep "$(date '+%Y-%m-%d')" ~/.local/share/recon/logs/recon.log | grep "ERR:" | wc -l

# Check config file permissions (P0 if not 0600)
stat -c "%a %n" ~/.config/recon/config.toml

# Check for unexpected network connections (possible key leak)
netstat -tulpn 2>/dev/null | grep python3 || ss -tulpn | grep python3
```

---

## 3. Incident Response Checklist

### 3.1 Universal Response Steps (All Severities)

```bash
# Step 1: STOP — Do not panic. Do not make random changes.
echo "INCIDENT: $(date) — Starting response checklist"

# Step 2: Document start time
START_TIME=$(date +%s)
echo "Incident start: $(date -Iseconds)" > /tmp/recon_incident_$(date +%Y%m%d_%H%M%S).log

# Step 3: Preserve current state
cd ~/Projects/recon
git status > /tmp/recon_incident_git_status.log
git log --oneline -5 >> /tmp/recon_incident_git_status.log
pip freeze > /tmp/recon_incident_pip_freeze.log

# Step 4: Check logs for immediate clues
tail -n 100 ~/.local/share/recon/logs/recon.log > /tmp/recon_incident_last_logs.log

# Step 5: Run health check
pytest -x --tb=short >> /tmp/recon_incident_health.log 2>&1 || echo "TESTS FAILED"

# Step 6: Determine severity (see Section 1)
# P0 = data loss / security breach
# P1 = completely broken
# P2 = partially degraded
# P3 = cosmetic
```

### 3.2 P0 — Critical Response Checklist

```bash
# P0: Data Loss / Security Breach

# Step 1: ISOLATE
# If keys leaked, disconnect from network immediately
# sudo systemctl stop NetworkManager  # Only if confirmed breach

# Step 2: PRESERVE EVIDENCE
cp ~/.config/recon/config.toml /tmp/recon_incident_config_compromised_$(date +%s).bak
cp ~/.local/share/recon/cache.db /tmp/recon_incident_db_compromised_$(date +%s).bak
tar czf /tmp/recon_incident_evidence_$(date +%s).tar.gz ~/.local/share/recon/logs/

# Step 3: REVOKE KEYS IMMEDIATELY
# USPTO: https://developer.uspto.gov/ → My Apps → Revoke
# EPO: https://developers.epo.org/ → Revoke
# Lens.org: https://www.lens.org/lens/user/subscriptions → Revoke

# Step 4: DELETE LOCAL KEYS
shred -u ~/.config/recon/config.toml
rm -f ~/.config/recon/config.toml.bak.*

# Step 5: VERIFY NO OTHER COPIES
grep -r "YOUR_OLD_KEY" ~/.config/ ~/.local/share/recon/ ~/Projects/recon/ 2>/dev/null || echo "No key remnants found"

# Step 6: GENERATE NEW KEYS
# Follow provider portal instructions

# Step 7: RECONFIGURE
recon config set --uspto-key NEW_KEY
recon config set --epo-consumer-key NEW_KEY
recon config set --epo-consumer-secret NEW_SECRET
chmod 600 ~/.config/recon/config.toml

# Step 8: VERIFY
recon config show
recon search "test"

# Step 9: DOCUMENT
# Fill out Postmortem Template (Section 7)
```

### 3.3 P1 — High Response Checklist

```bash
# P1: Core Functionality Broken

# Step 1: IDENTIFY LAST KNOWN GOOD
cd ~/Projects/recon
git log --oneline -10

# Step 2: STASH CURRENT WORK
git stash push -m "emergency-stash-$(date +%Y%m%d-%H%M%S)"

# Step 3: ROLLBACK TO LAST KNOWN GOOD
git reset --hard HEAD~1
# OR: git checkout COMMIT_HASH

# Step 4: REINSTALL
source .venv/bin/activate
pip install -e . --force-reinstall --no-deps

# Step 5: VERIFY
pytest -xvs
recon search "test"

# Step 6: IF STILL BROKEN, GO BACK FURTHER
git log --oneline -20
git reset --hard HEAD~2
# Repeat Steps 4-5

# Step 7: ONCE WORKING, INVESTIGATE
# Compare broken vs working:
git diff HEAD~1 HEAD -- tui/screens.py
# OR: git bisect start; git bisect bad; git bisect good HEAD~5

# Step 8: FIX FORWARD
git stash pop  # Restore your work
git checkout -b fix/incident-$(date +%Y%m%d)
# Apply targeted fix
# Test
# Commit
# Merge
```

### 3.4 P2 — Medium Response Checklist

```bash
# P2: Partial Degradation

# Step 1: IDENTIFY SCOPE
# Which API is down?
recon search "test" --source uspto  # Test USPTO
recon search "test" --source wipo    # Test WIPO
recon search "test" --source epo     # Test EPO

# Step 2: CHECK PROVIDER STATUS
# USPTO: https://developer.uspto.gov/api-status
# EPO: https://developers.epo.org/help/faq.html
# WIPO: https://www.wipo.int/patentscope/

# Step 3: WORKAROUND — USE OTHER SOURCES
# Edit ~/.config/recon/config.toml to disable broken source temporarily
# Or use CLI flag: recon search "query" --source wipo,google

# Step 4: DOCUMENT WORKAROUND
cat >> ~/Projects/recon/KNOWN_ISSUES.md << 'EOF'
## $(date +%Y-%m-%d): [P2] USPTO API Degraded
- **Symptom:** USPTO searches return ERR: or timeout
- **Workaround:** Use `--source wipo,epo` flag
- **Status:** Monitoring provider status page
- **ETA:** Unknown (external dependency)
EOF

# Step 5: MONITOR
tail -f ~/.local/share/recon/logs/recon.log | grep -i "uspto\|timeout\|429"

# Step 6: VERIFY RESOLUTION (when provider fixes)
recon search "test" --source uspto
# If works, update KNOWN_ISSUES.md
```

### 3.5 P3 — Low Response Checklist

```bash
# P3: Cosmetic / Minor

# Step 1: VERIFY IT'S ACTUALLY P3
# Does it block any workflow? Does it cause data loss?
# If NO to both → P3 confirmed

# Step 2: DOCUMENT IN BACKLOG
cat >> ~/Projects/recon/BACKLOG.md << 'EOF'
## $(date +%Y-%m-%d): [P3] DESCRIPTION
- **Severity:** P3
- **Impact:** Cosmetic
- **Repro:** Steps to reproduce
- **Priority:** Next polish session
EOF

# Step 3: FIX WHEN CONVENIENT
# No urgency. Do NOT interrupt current work.

# Step 4: CLOSE WHEN FIXED
git commit -m "fix(p3): DESCRIPTION"
```

---

## 4. Escalation Matrix

| Severity | Primary Responder | Secondary | External | Response Time | Communication |
|---|---|---|---|---|---|
| **P0** | You (Solo Maintainer) | N/A — you are the only responder | USPTO/EPO/Lens security teams (if keys leaked) | Immediate | GitHub private security advisory |
| **P1** | You (Solo Maintainer) | N/A | API provider support (if provider-side bug) | < 1 hour | GitHub Issue (public if not security) |
| **P2** | You (Solo Maintainer) | N/A | API provider status page / community forums | < 4 hours | GitHub Discussion or Issue |
| **P3** | You (Solo Maintainer) | N/A | None | < 24 hours | GitHub Issue with `p3` label |

### Escalation Flowchart

```
Incident Detected
  ├─ P0 (Critical)
  │   ├─ Immediate: You respond
  │   ├─ If keys leaked: Contact API provider security team
  │   └─ Post-resolution: File GitHub security advisory
  │
  ├─ P1 (High)
  │   ├─ You respond within 1 hour
  │   ├─ If provider-side: Open support ticket with API provider
  │   └─ Post-resolution: Public GitHub Issue
  │
  ├─ P2 (Medium)
  │   ├─ You respond within 4 hours
  │   ├─ Workaround documented in KNOWN_ISSUES.md
  │   └─ Monitor provider status
  │
  └─ P3 (Low)
      ├─ You respond within 24 hours
      └─ Add to BACKLOG.md
```

### External Contact Information

| Provider | Support URL | Security Contact |
|---|---|---|
| **USPTO** | https://developer.uspto.gov/contact | security@uspto.gov |
| **EPO** | https://developers.epo.org/contact | security@epo.org |
| **WIPO** | https://www.wipo.int/contact/ | N/A |
| **GitHub** | https://support.github.com | https://github.com/security/advisories |

---

## 5. Communication Templates

### 5.1 GitHub Issue — Bug Report (P1/P2)

```markdown
## Incident Report: [BRIEF DESCRIPTION]

**Severity:** P1 / P2 / P3
**Date:** YYYY-MM-DD HH:MM UTC
**Status:** Investigating / Identified / Monitoring / Resolved

### Summary
[One-paragraph description of what happened and impact.]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should have happened.]

### Actual Behavior
[What actually happened. Include error messages.]

### Environment
- RECON version: [e.g., 0.2.0]
- Python version: [e.g., 3.12.4]
- OS: [e.g., Arch Linux]
- Terminal: [e.g., Kitty 0.35]

### Logs
```
[Paste relevant log lines from ~/.local/share/recon/logs/recon.log]
```

### Workaround
[If any, describe how users can work around the issue.]

### Resolution
[To be filled when resolved.]
```

### 5.2 GitHub Security Advisory (P0 Only)

```markdown
## Security Advisory: [CVE or Internal ID]

**Severity:** P0 — Critical
**Date:** YYYY-MM-DD
**Affected Versions:** [e.g., 0.2.0 and earlier]
**Patched Version:** [e.g., 0.2.1]

### Summary
[Brief description of the vulnerability.]

### Impact
[What data or functionality is at risk.]

### Attack Vector
[How an attacker could exploit this.]

### Mitigation (Immediate)
[Steps users should take RIGHT NOW.]

### Fix
[Technical details of the fix.]

### Timeline
- YYYY-MM-DD HH:MM — Issue discovered
- YYYY-MM-DD HH:MM — Fix committed
- YYYY-MM-DD HH:MM — Patch released
- YYYY-MM-DD HH:MM — Advisory published

### Credits
[Reporter name, if external.]
```

### 5.3 Internal Status Update (Solo Maintainer Log)

```markdown
## Status Update: [INCIDENT_NAME] — $(date +%Y-%m-%d\ %H:%M)

**Severity:** P0 / P1 / P2 / P3
**Status:** 🔴 Investigating / 🟡 Identified / 🟢 Monitoring / ⚪ Resolved

### Current State
[What you know right now.]

### Actions Taken
- [Action 1 with timestamp]
- [Action 2 with timestamp]

### Next Steps
- [Step 1]
- [Step 2]

### ETA for Resolution
[Best guess, or "unknown".]

### Lessons So Far
[What you've learned. Update as you go.]
```

### 5.4 User-Facing Update (If Community Exists)

```markdown
## [RESOLVED] Brief Description of Incident

**What happened:** [One sentence.]
**Impact:** [Who was affected and how.]
**Root cause:** [Technical explanation, no blame.]
**Fix applied:** [What was changed.]
**Prevention:** [What we're doing to prevent recurrence.]

We apologize for any inconvenience. Full postmortem: [link].
```

---

## 6. War Room Protocol

**For RECON, the "war room" is your terminal.** There is no team call. This section documents how to run a focused, disciplined incident response as a solo maintainer.

### 6.1 War Room Setup

```bash
# Create a dedicated workspace for the incident
mkdir -p ~/incidents/recon-$(date +%Y%m%d-%H%M%S)
cd ~/incidents/recon-$(date +%Y%m%d-%H%M%S)

# Open three terminal panes/tabs:
# Pane 1: Logs
tail -f ~/.local/share/recon/logs/recon.log

# Pane 2: Health checks (run repeatedly)
watch -n 5 'cd ~/Projects/recon && source .venv/bin/activate && pytest -x --tb=line && echo "OK" || echo "FAIL"'

# Pane 3: Investigation and fixes
```

### 6.2 War Room Rules

| Rule | Rationale |
|---|---|
| **No code edits without a test** | Every fix must be verified by `pytest` |
| **One change at a time** | If you break more, you can't bisect |
| **Document every command** | Paste into incident log file |
| **Set a timer** | If stuck > 30 min, escalate to rollback |
| **No `git push` until verified** | Local fix first, push after tests pass |
| **Take screenshots** | Visual evidence for postmortem |

### 6.3 War Room Checklist

```bash
# Before starting fixes:
[ ] Incident log file created
[ ] Current state backed up (git stash, config backup)
[ ] Three terminal panes open (logs, health, fixes)
[ ] Timer set for 30 minutes

# During response:
[ ] Every command logged to incident file
[ ] Tests run after every change
[ ] No changes to unrelated files
[ ] Git commits are small and descriptive

# Before declaring resolved:
[ ] Full test suite passes: pytest -xvs
[ ] Smoke test passes: recon search "test"
[ ] Logs show no ERR: entries
[ ] Incident log file complete
[ ] Postmortem template started
```

### 6.4 War Room Shutdown

```bash
# When incident is resolved:

# 1. Final verification
pytest -xvs
recon search "test"

# 2. Commit all fixes
cd ~/Projects/recon
git add .
git commit -m "fix(incident): [BRIEF DESCRIPTION]

- Root cause: [WHAT WENT WRONG]
- Fix: [WHAT CHANGED]
- Verification: [HOW CONFIRMED]

Refs: incident-$(date +%Y%m%d-%H%M%S)"

# 3. Push
git push origin main

# 4. Close incident log
echo "Incident resolved: $(date -Iseconds)" >> ~/incidents/recon-$(date +%Y%m%d-%H%M%S)/incident.log

# 5. Schedule postmortem (within 24 hours)
echo "Postmortem due: $(date -d '+24 hours' -Iseconds)" >> ~/incidents/recon-$(date +%Y%m%d-%H%M%S)/incident.log
```

---

## 7. Postmortem Template

```markdown
# Postmortem: [INCIDENT_TITLE]

| Field | Value |
|---|---|
| **Incident ID** | RECON-YYYYMMDD-NNN |
| **Date** | YYYY-MM-DD |
| **Severity** | P0 / P1 / P2 / P3 |
| **Duration** | HH:MM (from detection to resolution) |
| **Reporter** | [Who found it] |
| **Responder** | [You] |

---

## Summary

[One-paragraph summary of what happened, impact, and resolution. Write this for someone who knows nothing about the incident.]

---

## Timeline (All times in UTC)

| Time | Event | Actor |
|---|---|---|
| HH:MM | [Detection event] | [Who/what detected] |
| HH:MM | [First response action] | [You] |
| HH:MM | [Key discovery or decision] | [You] |
| HH:MM | [Fix applied] | [You] |
| HH:MM | [Verification complete] | [You] |
| HH:MM | [Incident declared resolved] | [You] |

---

## Root Cause Analysis

### What Went Wrong

[Detailed technical explanation. Be specific: file names, line numbers, function names, error messages.]

### Why It Went Wrong

[Underlying cause. Was it a code bug? Config error? External dependency failure? Human error?]

### Why We Didn't Catch It Earlier

[Why didn't tests catch this? Why didn't the user notice sooner? What monitoring gap existed?]

---

## Impact Assessment

| Category | Impact |
|---|---|
| **Data Loss** | [None / X records / Unknown] |
| **Functionality** | [None / Partial / Complete outage] |
| **Users Affected** | [0 / 1 (you) / N] |
| **API Keys Compromised** | [No / Yes — rotated / Yes — investigating] |
| **Time Lost** | [HH:MM] |

---

## Resolution

### What Fixed It

[Exact fix applied. Include commit hash if applicable.]

### Verification

[How you confirmed the fix worked. Test output, log entries, manual checks.]

---

## Action Items

| # | Action | Owner | Due Date | Status |
|---|---|---|---|---|
| 1 | [Specific, measurable action] | [You] | YYYY-MM-DD | ⬜ / ✅ |
| 2 | [Specific, measurable action] | [You] | YYYY-MM-DD | ⬜ / ✅ |
| 3 | [Specific, measurable action] | [You] | YYYY-MM-DD | ⬜ / ✅ |

---

## Lessons Learned

### What Went Well

- [Something that worked during response]

### What Went Poorly

- [Something that slowed response or made it harder]

### What We Need to Improve

- [Process, monitoring, or code change needed]

---

## Blameless Analysis

[This section explicitly states that no individual is at fault. Focus on system failures, not personal failures.]

> "The issue was caused by [system condition], not by [person]. [Person] made a reasonable decision given the information available at the time. The system should have prevented this or made it more visible."

---

## Appendix

### Relevant Logs

```
[Paste key log excerpts]
```

### Relevant Code

```python
[Paste relevant code snippets]
```

### Relevant Commands

```bash
[Paste commands run during response]
```

---

*Postmortem completed: YYYY-MM-DD*
*Reviewed by: [You]*
*Next review: YYYY-MM-DD (30 days)*
```

---

## 8. Blameless Culture Guidelines

### 8.1 Core Principles

| Principle | Application |
|---|---|
| **Human error is a symptom** | If a person made a mistake, the system allowed it. Fix the system. |
| **No naming names in postmortems** | Use roles ("the maintainer", "the user") not names. |
| **Assume good intent** | Every decision was reasonable given available information. |
| **Focus on systems, not individuals** | "The test didn't catch this" not "You didn't write a test." |
| **Share widely** | Postmortems are learning opportunities, not performance reviews. |

### 8.2 Language Guide

| ❌ Blameful | ✅ Blameless |
|---|---|
| "You broke the build." | "The build broke because the test suite didn't cover this edge case." |
| "I forgot to rotate the key." | "The key rotation process had no automated reminder or check." |
| "The user did something stupid." | "The CLI allowed an invalid input without validation or clear error messaging." |
| "Someone committed bad code." | "The code review process didn't catch the missing bounds check." |
| "It was my fault." | "The system lacked safeguards that would have prevented this." |

### 8.3 Blameless Postmortem Checklist

```bash
# Before publishing a postmortem, verify:

# 1. No individual names (except reporter/responder roles)
grep -i "anubhavaanand\|you\|i" postmortem.md || echo "No personal names found"

# 2. Every "what went wrong" has a corresponding system fix
# 3. Action items are specific and assigned
# 4. The tone is factual, not emotional
# 5. The postmortem is shared (GitHub Issue or docs/)
```

### 8.4 When You Are the Only Person

Even as a solo maintainer, write postmortems in third person:

> "The maintainer deployed without running the full test suite. The CI pipeline should have blocked this."

This trains the habit for when you have collaborators, and it creates distance for clearer analysis.

---

## 9. Common Incident Playbooks

### 9.1 Playbook: Corrupted SQLite Cache Database

```bash
# DETECTION:
# - "sqlite3.OperationalError: database is malformed"
# - recon search crashes with DB error
# - cache.db size is 0 bytes or extremely large

# RESPONSE:

# Step 1: Preserve corrupted DB
CORRUPTED=~/.local/share/recon/cache.db
BACKUP=~/.local/share/recon/cache.db.corrupt.$(date +%s)
cp "$CORRUPTED" "$BACKUP"

# Step 2: Attempt SQLite repair
sqlite3 "$CORRUPTED" ".recover" | sqlite3 ~/.local/share/recon/cache.db.recovered

# Step 3: Verify recovered DB
sqlite3 ~/.local/share/recon/cache.db.recovered ".tables"

# Step 4: If repair works, swap in
mv ~/.local/share/recon/cache.db.recovered "$CORRUPTED"

# Step 5: If repair fails, restore from backup
LATEST=$(ls -t ~/.local/share/recon/cache.db.bak.* 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    cp "$LATEST" "$CORRUPTED"
    echo "Restored from $LATEST"
else
    rm "$CORRUPTED"
    echo "No backup. Database will be recreated on next search."
fi

# Step 6: Verify
recon search "test"

# POSTMORTEM TRIGGER: P1 if no backup exists, P2 if restored from backup
```

### 9.2 Playbook: API Key Leaked in Public Repository

```bash
# DETECTION:
# - GitHub secret scanning alert
# - Accidental commit with config.toml
# - Key visible in git history

# RESPONSE:

# Step 1: IMMEDIATE — Revoke keys at provider portals
# USPTO: https://developer.uspto.gov/ → My Apps → Revoke
# EPO: https://developers.epo.org/ → Revoke

# Step 2: Rotate in GitHub history (if pushed)
cd ~/Projects/recon

# Install git-filter-repo if needed
# pip install git-filter-repo

# Remove file from history
git filter-repo --path ~/.config/recon/config.toml --invert-paths

# OR: Remove specific string
git filter-repo --replace-text <(echo "OLD_KEY==>REDACTED")

# Step 3: Force push (DESTRUCTIVE — coordinate if collaborators exist)
git push origin main --force

# Step 4: Delete local config
shred -u ~/.config/recon/config.toml

# Step 5: Generate new keys at provider portals

# Step 6: Reconfigure
recon config set --uspto-key NEW_KEY
chmod 600 ~/.config/recon/config.toml

# Step 7: Add to .gitignore if not already
grep "config.toml" .gitignore || echo "*.toml" >> .gitignore

# Step 8: Verify no keys in history
git log --all --full-history -- . | grep -i "key\|secret\|token" || echo "Clean"

# POSTMORTEM TRIGGER: P0
```

### 9.3 Playbook: All API Calls Failing (Rate Limit or Auth)

```bash
# DETECTION:
# - Every search returns "ERR: Source [X] failed"
# - Logs show 429 or 401 errors
# - recon search "test" returns empty results

# RESPONSE:

# Step 1: Check which APIs are failing
for source in uspto wipo epo; do
    echo "Testing $source..."
    recon search "test" --source "$source" 2>&1 | head -5
done

# Step 2: Check rate limit status
grep -i "429\|rate.limit\|backoff" ~/.local/share/recon/logs/recon.log | tail -20

# Step 3: Check key validity
recon config show
# Verify keys match what's shown in provider portals

# Step 4: Check provider status pages
# USPTO: https://developer.uspto.gov/api-status
# EPO: Check https://ops.epo.org/ health
# WIPO: Check https://www.wipo.int/patentscope/

# Step 5: If rate limited, wait and retry
# USPTO: 100/min limit, wait 60 seconds
# EPO: 4/sec limit, wait 15 seconds
# WIPO: 100/day limit, wait 24 hours

echo "Waiting 60 seconds for rate limit reset..."
sleep 60
recon search "test"

# Step 6: If auth error, regenerate keys
# Follow provider portal instructions

# Step 7: If provider is down, use workaround
# recon search "query" --source wipo,epo  # Exclude broken source

# POSTMORTEM TRIGGER: P1 if auth/key issue, P2 if provider down
```

### 9.4 Playbook: TUI Completely Unresponsive

```bash
# DETECTION:
# - recon search opens but no keyboard input works
# - Screen is frozen or black
# - Process uses 100% CPU

# RESPONSE:

# Step 1: Check if process is alive
pgrep -f "recon search"

# Step 2: If alive but hung, attach strace
sudo strace -p $(pgrep -f "recon search") 2>&1 | head -20

# Step 3: Kill the process
pkill -9 -f "recon search"

# Step 4: Check terminal state
stty sane
reset

# Step 5: Test in minimal environment
TERM=xterm-256color recon search

# Step 6: Check for display issues
# Kitty: kitty +kitten icat --test  # Test image protocol
# iTerm2: Check "Inline Images" setting

# Step 7: If still broken, check for recent changes
cd ~/Projects/recon
git diff HEAD~1 -- tui/screens.py tui/app.py

# Step 8: Rollback if needed
git stash
git checkout HEAD~1 -- tui/screens.py tui/app.py
pip install -e . --force-reinstall --no-deps

# Step 9: Verify
recon search

# POSTMORTEM TRIGGER: P1 if no workaround, P2 if terminal-specific
```

### 9.5 Playbook: Dependency CVE Detected

```bash
# DETECTION:
# - pip-audit reports CVE
# - GitHub Dependabot alert
# - safety check failure

# RESPONSE:

# Step 1: Identify affected package and CVE
pip-audit --desc

# Step 2: Check if RECON actually uses the vulnerable code path
# Example: CVE in Pillow's image parsing
grep -r "Image.open\|Image.load" tui/widgets/image_tab.py

# Step 3: If vulnerable path is used, update immediately
source .venv/bin/activate
pip install --upgrade Pillow

# Step 4: Run tests to verify no breakage
pytest -xvs

# Step 5: If update breaks compatibility, pin to safe version
# Edit pyproject.toml: "Pillow>=10.0.0,<11.0.0"
pip install -e .

# Step 6: Commit and push
git add pyproject.toml
git commit -m "security: bump Pillow to patch CVE-XXXX-XXXX

- Vulnerability: [DESCRIPTION]
- Affected: [VERSION RANGE]
- Patched: [NEW VERSION]
- Verification: pytest -xvs passes"
git push origin main

# Step 7: Document in CHANGELOG.md
# Add to [Unreleased] > Security section

# POSTMORTEM TRIGGER: P0 if actively exploited, P1 if patch available, P2 if no known exploit
```

### 9.6 Playbook: Export Produces Corrupt File

```bash
# DETECTION:
# - Exported JSON is not valid JSON
# - PDF export is blank or malformed
# - CSV has wrong column alignment

# RESPONSE:

# Step 1: Identify export format and corruption type
recon export --format json --output test.json
python3 -m json.tool test.json > /dev/null && echo "JSON valid" || echo "JSON INVALID"

# Step 2: Check source data
cat ~/.local/share/recon/collection_export.json | head -20

# Step 3: Check for special characters in patent data
grep -P '[^ -]' ~/.local/share/recon/collection_export.json | head -5

# Step 4: Fix encoding issues in export formatter
# Edit cli/export.py — add encoding="utf-8" or sanitize special chars

# Step 5: Test all formats
for fmt in json csv pdf md bibtex; do
    recon export --format "$fmt" --output "test.$fmt"
    echo "$fmt: $?"
done

# Step 6: If PDF is broken, check fpdf2 version
pip show fpdf2

# Step 7: Commit fix
git add cli/export.py
git commit -m "fix(export): handle special characters in patent data

- Root cause: Unicode chars in titles/abstracts broke JSON/PDF
- Fix: Added utf-8 encoding and character sanitization
- Verification: All 5 export formats tested"

# POSTMORTEM TRIGGER: P2 if workaround exists (use other format), P1 if all formats broken
```

---

## 10. Post-Incident Review Process

### 10.1 Review Schedule

| Severity | Review Timing | Attendees | Output |
|---|---|---|---|
| **P0** | Within 24 hours | You (solo) + any affected users | Postmortem + action items |
| **P1** | Within 48 hours | You (solo) | Postmortem + action items |
| **P2** | Within 1 week | You (solo) | Brief summary + 1-2 action items |
| **P3** | Next polish session | You (solo) | GitHub Issue comment |

### 10.2 Review Checklist

```bash
# Before the review:
[ ] Incident log file is complete
[ ] Postmortem template is filled
[ ] All action items have owners and due dates
[ ] No blameful language in postmortem

# During the review:
[ ] Timeline is accurate (verify against logs)
[ ] Root cause is specific (file names, line numbers)
[ ] Impact is quantified (time lost, data affected)
[ ] Action items are specific and measurable
[ ] At least one action item prevents recurrence
[ ] At least one action item improves detection

# After the review:
[ ] Postmortem published (GitHub Issue or docs/postmortems/)
[ ] Action items added to project backlog
[ ] Due dates set in calendar
[ ] Follow-up scheduled (30 days)
```

### 10.3 Review Questions

Answer these for every incident:

1. **Detection:** How was the incident discovered? Could we have found it sooner?
2. **Response:** How long from detection to first action? What slowed us down?
3. **Resolution:** What actually fixed it? Was the first fix the right fix?
4. **Prevention:** What system change would prevent this exact incident?
5. **Detection (future):** What monitoring or alert would catch this next time?
6. **Process:** Did any runbook step help or hinder? What should change?

### 10.4 Action Item Tracking

```bash
# Create action item file
cat > ~/Projects/recon/docs/action_items_$(date +%Y%m%d).md << 'EOF'
# Action Items: [INCIDENT_NAME]

| # | Action | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| 1 | [Specific action] | You | YYYY-MM-DD | ⬜ | [Link to commit/PR] |
| 2 | [Specific action] | You | YYYY-MM-DD | ⬜ | [Link to commit/PR] |

## Verification Commands

```bash
# Run these to verify action items are complete:
pytest -xvs  # All tests pass
recon search "test"  # Smoke test passes
grep "ERR:" ~/.local/share/recon/logs/recon.log | wc -l  # Should be 0
```
EOF

# Review weekly
cat ~/Projects/recon/docs/action_items_*.md
```

### 10.5 Continuous Improvement

```bash
# Monthly: Review all incidents
cd ~/Projects/recon
git log --oneline --grep="fix\|incident\|hotfix" --since="30 days ago"

# Quarterly: Update playbooks based on new incident types
# - Add new playbook if novel incident occurred
# - Update existing playbook if steps were wrong
# - Remove playbook if no longer relevant

# Annually: Full IR document review
# - Verify all contact information
# - Test all rollback procedures
# - Update severity examples based on history
```

---

## Appendix A: Quick Reference

| Situation | Immediate Action | Section |
|---|---|---|
| Tool won't start | `pytest -x --tb=short` | 3.3 |
| Keys might be leaked | `shred -u ~/.config/recon/config.toml` | 3.2 |
| Database error | `cp cache.db cache.db.bak; sqlite3 cache.db ".recover"` | 9.1 |
| All APIs failing | Check `recon config show` and provider status | 9.3 |
| TUI frozen | `pkill -9 -f "recon search"; stty sane` | 9.4 |
| CVE alert | `pip-audit --desc; pip install --upgrade PACKAGE` | 9.5 |
| Export broken | `recon export --format json; python3 -m json.tool` | 9.6 |
| Don't know severity | Run health check, see flowchart in Section 1 | 1 |
| Need to rollback | `git stash; git reset --hard HEAD~1` | 3.3 |
| Need logs | `tail -n 100 ~/.local/share/recon/logs/recon.log` | 8 |

## Appendix B: File Locations

| File | Path | Purpose |
|---|---|---|
| Config | `~/.config/recon/config.toml` | API keys, settings |
| Database | `~/.local/share/recon/cache.db` | Search cache, collections |
| Logs | `~/.local/share/recon/logs/recon.log` | Application logs |
| Backups | `~/.local/share/recon/backups/` | Database backups |
| Incidents | `~/incidents/recon-YYYYMMDD-HHMMSS/` | Incident workspaces |
| Postmortems | `~/Projects/recon/docs/postmortems/` | Published postmortems |
| Action Items | `~/Projects/recon/docs/action_items_*.md` | Tracking |

---

*Document Owner: Solo Maintainer | Review Cycle: Quarterly | Next Review: 2026-09-22*
