# Architecture

## Layers

- `cli/` — Typer CLI surface and export logic
- `tui/` — Textual app, screens, widgets
- `core/` — scoring, search, translation, enrichment, models
- `clients/` — httpx clients, scrapers, circuit breaker
- `storage/` — SQLite cache, migrations, eviction

## Data Flow

1. CLI/TUI constructs a `SearchQuery`.
2. `core.search.SearchEngine` fans out to enabled sources.
3. Results normalize into `core.models.PatentDocument`.
4. Scoring applies equal-weight signals (+20 each).
5. Storage caches raw responses and terminal sessions.
6. UI renders sorted results; export writes PDF/JSON/Markdown.

## Conventions

- No AI-by-default paths in hot paths.
- Deterministic sorting: descending score, never drop records.
- Terminal-native rendering; no ModalScreen.
- Errors: `ERR:` prefix, terse, actionable.
