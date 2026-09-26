# searinks

Seattle-area ice rink schedules in one place: Kraken Community Iceplex, Sno-King Kirkland, Renton and Snoqualmie, Olympic View Arena and Lynnwood Ice Center.

## View the schedules

**https://anne-xie.github.io/searinks/**

Works on phones and desktop. No sign-in needed.

> Not live yet: GitHub Pages is turned on in #22.

## Data and refresh schedule

A GitHub Action fetches every rink's schedule for the next 14 days from the rinks' booking systems, then redeploys the site with fresh data. It runs:

- every 3 hours
- on every push to `main`
- on demand: **Actions → publish → Run workflow**, or `gh workflow run publish.yml --repo anne-xie/searinks`

The site shows when its data was last updated. The latest data dump is published alongside the site as JSON:

- `https://anne-xie.github.io/searinks/data/rinks.json`: rink list (name, area, coordinates, sheets)
- `https://anne-xie.github.io/searinks/data/days/<YYYY-MM-DD>/<rink>.json`: one rink's sessions for one day, e.g. `days/2026-09-26/kraken.json`

> Not live yet: the Action is added in #21.

To make a fresh dump locally instead, run `uv run searinks-export`. It writes the same files to `site/data/` (`--days N` changes the range, `--rink KEY` limits it to some rinks).

## Development

Print schedules in the terminal:

```bash
uv run searinks kraken kirkland --date 2026-09-26 --days 3 --drop-in --sport hockey
```

Omit the rinks to query all of them (`kraken`, `kirkland`, `renton`, `snoqualmie`, `ova`, `lynnwood`).

- `--search TEXT` case-insensitive title filter
- `--drop-in` only sessions sold per visit
- `--sport hockey|figure|public` only that discipline

Run the site locally (Vite + Preact in `web/`, reading `site/data/`):

```bash
uv run searinks-export --days 2
cd web && npm install && npm run dev
```

Tests: `uv run pytest` and `cd web && npm test`
