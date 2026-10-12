# Evaluation

## Test Strategy

- Unit tests for scoring, models, cache, config, translation.
- Integration tests for CLI and storage flows.
- TUI tests use Textual pilot/snapshot harness.

## Coverage Target

Run:

```bash
python -m pytest tests/ \
  --cov=cli \
  --cov=tui \
  --cov=core \
  --cov=clients \
  --cov=storage \
  --cov-report=term \
  --cov-fail-under=80
```

## Constitution Checks

- No `ModalScreen` usage.
- No `.get_item_at()` in ListView code.
- No unauthorized AI provider imports outside exempt modules.
- No bare `except Exception: pass`.

## Performance

- Prefer fast first responses.
- Lazy-load deep claims/images.
- Cache TTL governs staleness, not silent imputation.
