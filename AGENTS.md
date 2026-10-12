# RECON Project - Agent Instructions

## Project
Terminal-native patent research CLI/TUI tool. Python 3.12+, Textual, httpx, Pillow, rapidfuzz, typer, SQLite.

## Constitution (must follow)
1. **Zero-AI Default** - Fully deterministic, no hidden LLM layers
2. **Transparency** - Present data as retrieved, never persuade
3. **Equal Signal Weights** - All scoring signals weighted equally (+20 each)
4. **Descending Sort, Never Removing** - Results sorted desc, never silently dropped
5. **Terminal-Native** - CLI only, no GUI fallback
6. **Speed over Depth** - Fast first responses, lazy loading for deep data
7. **Uncertainty Flagged** - Missing data marked `[?]` or `UNKNOWN`, never imputed
8. **Dry, Actionable Errors** - Terse, factual, no apologies, exact reason + resolution

## Key Files
- Constitution: `.specify/docs/constitution.md`
- Spec: `.specify/docs/spec.md`
- Evaluation Framework: `.specify/docs/evaluation-framework.md`
- Tasks: `.specify/tasks/EVALUATION_TASKS.md`
- PRD: `RECON_PRD_v1.0.0.md`

## Tasks
Execute in order: Phase A (Foundation) -> Phase B (Component) -> Phase C (Advanced) -> Phase D (Automation)

## Skills Available
test-driven-development, executing-plans, writing-plans, systematic-debugging, verifying-before-completion, subagent-driven-development, requesting-code-review, internet-researcher, processing-pdf, configuring-opencode

## Agents Available
@implementer, @spec-reviewer, @code-reviewer, @internet-researcher

## Textual TUI Best Practices (CRITICAL)
1. **No ModalScreens:** The project constitution explicitly forbids `ModalScreen`. If an overlay or dialog is needed (e.g., Export selector, Help menu), use an inline `Static` widget with `layer` and `dock` CSS positioning, toggled via a CSS class.
2. **Dry Error Voice:** All user-facing errors must start with `ERR:` and be terse and actionable. Never dump Python stack traces into the UI.
3. **ListView Navigation:** Use `self.highlighted_child` to get the currently selected item in a `ListView` and access by index via `self.children[self.index]`. Do not use `.get_item_at()`.
4. **TabbedContent:** Textual auto-prefixes tab IDs with `--content-tab-`. Strip this prefix before running matching logic.
5. **Reactive Attributes:** Rely on `reactive` attributes to trigger automatic UI updates when underlying data changes instead of manually updating widgets.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
