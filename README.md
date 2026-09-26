# searinks

Ice rink schedules from DaySmart Recreation. Supports Kraken Community Iceplex (`kraken`) and Sno-King Ice Arenas (`snoking`: Kirkland, Renton, Snoqualmie).

```bash
uv run searinks kraken snoking --date 2026-09-26 --days 3 --drop-in --sport hockey
```

Omit the rinks to query all of them.

- `--search TEXT` case-insensitive title filter
- `--drop-in` only sessions sold per visit
- `--sport hockey|figure|public` only that discipline

Tests: `uv run pytest`
