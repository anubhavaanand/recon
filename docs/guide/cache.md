# Data and Cache

## Cache DB

- Default path: `recon_cache.db`
- Stores raw API responses and terminal sessions.
- Eviction enforces `max_size_mb` by TTL and size.

## Terminal Sessions

Saved search runs are appended to `terminal_sessions` for replay.

## Maintenance

```bash
recon config --prune
```

## Limits

- Cache is not a replacement for offline archives.
- Missing data is flagged `[?]`, never imputed.
