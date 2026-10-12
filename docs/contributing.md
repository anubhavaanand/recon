# Contributing

## Branching

Use feature branches off `main`:

```bash
git checkout -b feat/<slug>
```

## Tests

Run the full suite before pushing:

```bash
python -m pytest tests/ -v
```

## Lint

```bash
ruff check .
mypy cli tui core clients storage
```

## Commits

Use Conventional Commits:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code change
- `test:` test addition
- `chore:` maintenance

## PRs

- Keep PRs under 400 lines when possible.
- Include rationale in the description.
- Ensure CI is green.

For full policy, see root [CONTRIBUTING.md](../CONTRIBUTING.md).
