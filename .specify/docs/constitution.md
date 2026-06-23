# RECON Constitution

## Core Principles

### I. Zero-AI Default
The system operates completely deterministically by default. No hidden LLM layers, predictive models, or semantic matching unless explicitly requested and sandboxed by the user.

### II. Transparency over Persuasion
Present data exactly as retrieved. Do not attempt to convince the user of a patent's relevance. Let the data and metadata speak for themselves.

### III. Equal Signal Weights
No hidden scoring algorithms or black-box ranking. All search signals and matching metadata are weighted equally.

### IV. Descending Sort, Never Removing Entries
Results are sorted descending by default. Filtering and sorting may demote items, but the tool will never silently drop or remove entries from the result set.

### V. Terminal-Native & Keyboard-First
Designed exclusively for the CLI with absolutely no GUI fallback. Operations must be fully accessible and optimized for keyboard-only workflows.

### VI. Speed over Depth
Prioritize fast initial responses and quick navigability over exhaustive, deep data retrieval. Fetch deep data only on explicit demand.

### VII. Uncertainty Flagged, Never Hidden
Missing data, ambiguous dates, or incomplete records must be explicitly marked. Never silently guess, impute, or omit uncertain data.

### VIII. Dry, Actionable Error Voice
Error messages must be terse, factual, and strictly actionable. No apologies, no conversational fluff. Provide exact reason and resolution steps.

## Stack Lock
Python 3.12+, Textual, httpx, Pillow, rapidfuzz, typer, SQLite.

## Prohibited
Modal dialogs hiding context, AI prose without data backing, signal omission, browser UI elements, GUI fallback, unequal weighting without override.

## Governance
This constitution supersedes all other design practices. Any new feature must be audited against these principles before implementation.

**Version**: 1.0.0 | **Ratified**: 2026-05-12

## Amendment 1 (Scraper Architecture)
The 8-package dependency limit is explicitly amended to include `beautifulsoup4`, `lxml`, and `ddgs` to support the required Scraper-First architecture pivot.
