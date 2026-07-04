## 2026-07-02 - [Added Async Loading Indicator]
**Learning:** In Textual apps, when updating the UI for background async tasks (like enrichment), always ensure state changes (e.g. `is_enriching = False`) are wrapped in a `finally` block. Otherwise, if the async task fails, the UI will permanently show the loading state, leading to a frustrating experience.
**Action:** Apply this to all background tasks affecting TUI state.
