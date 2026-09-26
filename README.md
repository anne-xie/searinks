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

## Web

A static site in `web/` (Vite + Preact) reads the JSON that `searinks-export` writes to `site/data/`.

```bash
uv run searinks-export --days 2
cd web && npm install && npm run dev
```

`npm run build` writes `web/dist/` (data included) for https://anne-xie.github.io/searinks/. Tests: `npm test`
