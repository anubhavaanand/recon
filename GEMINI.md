<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->

When helping with this repo, use this response structure:

1. Chronological review of what happened
2. Intent mapping for the user request
3. Technical inventory (libraries/tools involved)
4. Code archaeology (what was run, what failed, why)
5. Progress assessment (done vs blocked)
6. Context validation (what context is reliable)
7. Recent commands analysis
8. Clear continuation plan with immediate next actions

Troubleshooting defaults for local setup:
- Activate environment: `source venv/bin/activate`
- Install project: `python -m pip install -e '.[test]'`
- Run app module: `python -m recon`
- Run tests: `python -m pytest -q`

When errors appear, keep voice dry and actionable:
- State the exact failing command
- State the most likely root cause
- Give the next one or two concrete commands to run
