# Quick Start

## Install

### From PyPI

```bash
pip install recon-patent
```

### From source

```bash
git clone https://github.com/<org>/recon.git
cd recon
uv venv
uv pip install -e ".[test]"
```

## Run

```bash
recon --help
recon search "machine learning"
```

## TUI

```bash
recon run
```

## Configuration

Copy `.env.example` to `.env` and add optional API keys:

```bash
cp .env.example .env
```

Edit `config/config.ini` for defaults:

```ini
[search]
max_results = 50
cache_ttl_days = 7

[display]
theme = ansi
color = true
```

## Verify

```bash
python -m pytest tests/ -q
```
