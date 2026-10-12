# Configuration

## INI file

Default path: `config/config.ini`

```ini
[search]
max_results = 50
cache_ttl_days = 7
sources = uspto,epo,lens

[display]
theme = ansi
color = true

[cache]
path = recon_cache.db
max_size_mb = 500
```

## Environment

Copy `.env.example` to `.env` and fill keys:

```bash
USPTO_API_KEY=
EPO_CONSUMER_KEY=
EPO_CONSUMER_SECRET=
LENS_API_KEY=
PATSNAP_API_KEY=
DEEPSEEK_API_KEY=
NVIDIA_NIM_API_KEY=
```

Empty values fall back to keyless/default scraper mode.
