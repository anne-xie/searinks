# searinks

Seattle-area ice rink schedules. Supports Kraken Community Iceplex (`kraken`) and Sno-King Ice Arenas (`kirkland`, `renton`, `snoqualmie`) via DaySmart Recreation, and Olympic View Arena (`ova`) and Lynnwood Ice Center (`lynnwood`) via RecTimes.

```bash
uv run searinks kraken kirkland --date 2026-09-26 --days 3 --drop-in --sport hockey
```

Omit the rinks to query all of them.

- `--search TEXT` case-insensitive title filter
- `--drop-in` only sessions sold per visit
- `--sport hockey|figure|public` only that discipline

Tests: `uv run pytest`
