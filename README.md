# searinks

Seattle-area ice rink schedules in one place: Kraken Community Iceplex, Sno-King Kirkland, Renton and Snoqualmie, Olympic View Arena and Lynnwood Ice Center.

## View the schedules

**https://anne-xie.github.io/searinks/**

Works on phones and desktop. No sign-in needed.

> Not live yet: GitHub Pages is turned on in #22.

## Data and refresh schedule

Two GitHub Actions keep the site current while calling the rinks' booking systems as little as possible:

- **fetch-data** is the only one that calls them. It fetches every rink's schedule for the next 14 days and saves the result to the [`data` branch](https://github.com/anne-xie/searinks/tree/data). It runs:
  - twice a week, Monday and Thursday mornings (about 6am Pacific)
  - when a push to `main` changes the data sources (`src/searinks/`, e.g. adding a rink) or dependencies
  - on demand: **Actions → fetch-data → Run workflow**, or `gh workflow run fetch-data.yml --repo anne-xie/searinks`
- **deploy-site** rebuilds and publishes the site from the `data` branch without calling any APIs. It runs after every successful fetch-data run, when a push to `main` changes the site (`web/`), and on demand (`gh workflow run deploy-site.yml --repo anne-xie/searinks`).

If one rink can't be fetched, its previous data stays in place until the next run. The site shows when its data was last updated.

The latest data dump is JSON, on the `data` branch and alongside the site:

- `rinks.json`: rink list (name, area, coordinates, sheets)
- `days/<YYYY-MM-DD>/<rink>.json`: one rink's sessions for one day, e.g. `days/2026-09-26/kraken.json`

On the site these live under `https://anne-xie.github.io/searinks/data/`.

> Not live yet: both Actions are added in #21.

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
