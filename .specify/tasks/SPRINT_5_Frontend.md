# SPRINT 5: Frontend & UI Polish

## Objective
Read `.specify/docs/RECON_Frontend_Specification_v1.0.0.md` and implement the missing TUI interactions, responsive breakpoints, and specific styling dictated by the spec.

## Critical Requirements
1. **Search History Cycling:** In the main search `Input` widget, pressing the `Up` arrow should cycle backwards through the `search_history` database we built in Sprint 1.
2. **Missing Keybinds:** Implement `g` (jump to top of list), `G` (jump to bottom), and `a` (Assignee Portfolio View). Ensure pressing `q` dismisses any active inline overlays (export/source filters).
3. **Responsive Breakpoints:** The UI must react to terminal resizing. If `< 80` columns, the UI must collapse into a vertical stacked layout. If `< 40` columns, the app must gracefully exit with a message that the terminal is too small.
4. **CLI Flags & Fixes:** In `cli/main.py`, add `--file` for batch searches and `--format` (json/csv) to pipe to stdout. Also, fix the `recon search` CLI table so it displays the "Source" column instead of "Assignee".
5. **The Tokyo Night Palette:** `tui/styles.css` is currently using a generic GitHub Dark theme. You MUST rewrite the CSS variables to use the exact Tokyo Night palette specified in the docs (`$bg: #1a1b26`, `$primary: #7aa2f7`, etc.).
6. **"Dry" Error Voice:** Implement the exact error strings from the spec (e.g., `ERR: Query must be 3+ characters.`, `ERR: USPTO rate limited. Retrying in 2s...`, `ERR: Collection is empty. Save patents with 's' first.`). Ensure input validation turns the input border red.

## Instructions for OpenCode
Update `tui/screens.py`, `tui/styles.css`, and `cli/main.py`. Ensure the Constitution's "No ModalScreen" rule is preserved when adding the Assignee View (use hidden Static overlays instead).
