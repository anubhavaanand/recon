# Credential Rotation Procedure

## Critical Finding

A plaintext PatSnap API key was exposed in `.env` at the project root.

## Immediate Actions Required

### 1. Rotate the PatSnap API key

Log in to your PatSnap account and generate a new API key:
- Navigate to **Account Settings** → **API Access**
- Revoke the exposed PatSnap API key
- Generate a new key
- Update your local `.env` with the new value

### 2. Scan git history for the exposed key

```bash
git log -p --all -S 'PATSNAP_API_KEY'
```

Inspect the output for any commits that contain the actual key value. If found, rewrite history to remove `.env`:

```bash
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all
```

Or use `git filter-repo` if available:

```bash
git filter-repo --path .env --invert-paths
```

**Warning:** Rewriting history changes commit SHAs. Coordinate with any collaborators before force-pushing.

### 3. Force-push the cleaned history

```bash
git push origin --force --all
git push origin --force --tags
```

### 4. Verify `.env` is ignored

```bash
git check-ignore .env
```

Expected output: `.env`

### 5. Set restrictive permissions on local `.env`

```bash
chmod 600 .env
```

### 6. Audit for other credential leaks

Review all secret files for additional exposed keys:
```bash
grep -rE 'API_KEY|TOKEN|SECRET|PASSWORD' .env .env.local 2>/dev/null
```

## Prevention

- **Never** commit `.env` or any file containing secrets
- Use `recon config set --patsnap-key` for interactive key storage when possible
- Store production secrets in a secret manager (e.g., `~/.config/recon/config.toml` with `0600` permissions per ADR-019)
- Rotate any key that has ever appeared in a tracked file immediately

## References

- ADR-019: File-Based Secrets Over Environment Variables
- `docs/guide/config.md`
