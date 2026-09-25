# searinks

Ice rink schedules from DaySmart Recreation. Currently supports the Kraken Community Iceplex.

```bash
uv run searinks kraken --date 2026-09-26 --days 3 --drop-in --sport hockey
```

- `--search TEXT` case-insensitive title filter
- `--drop-in` only sessions sold per visit
- `--sport hockey|figure|public` only that discipline

Tests: `uv run pytest`
