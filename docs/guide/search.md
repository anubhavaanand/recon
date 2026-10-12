# Search and Export

## CLI

```bash
recon search "query" --source uspto --max-results 50
recon search "query" --source epo --format json
recon search "query" --source lens --export pdf
```

## Export

```bash
recon export --format pdf --output results.pdf
recon export --format json --output results.json
recon export --format md --output results.md
```

## Options

- `--source` limits to one provider.
- `--format` chooses CLI output or export serialization.
- `--max-results` caps the result set.
