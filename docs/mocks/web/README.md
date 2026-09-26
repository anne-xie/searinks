# Desktop web mocks (D2)

Finalized desktop layouts for the web frontend (tracking issue #17), designed at 1440px wide in the same D2 theme as the [phone mocks](../phone/README.md). Open any file in a browser; the nav links, Preferences button and rink links move between screens. Sample data is Sat Sep 26, 2026.

Source canvas: https://claude.ai/artifact/VsbPzaAqoaoC8YgT4qfUgd ("Desktop web mocks" row; the rows below it are explorations, not final). These files are static exports of that row; update both together.

| Screen | File | Tickets |
|--------|------|---------|
| Schedule: list and grid side by side | [schedule.html](schedule.html) | #12, #13 |
| Schedule with the date picker open | [schedule-date-picker.html](schedule-date-picker.html) | #12, #13 |
| Map and starred rinks | [map.html](map.html) | #14 |
| Preferences (dialog) | [preferences.html](preferences.html) | #15 |
| Preferences with the starred rinks panel expanded | [preferences-rinks.html](preferences-rinks.html) | #14, #15 |

## Design tokens

Same as the phone mocks. Extra desktop values:

| Token | Value |
|-------|-------|
| Top bar | white, 1px `#DCE8F3` bottom border |
| Active nav link | `#1F4FCC` text, 3px `#1F4FCC` underline |
| Scrollbar track / thumb | `#E7EFF7` / `#A9B7C6` |
| Grid sheet column | 180px fixed width |

## Decisions

- Web-style top bar: logo, text links for Schedule and Map, and a labeled Preferences button. No pill tabs.
- Schedule shows the list (left) and the grid (right) together, so there is no list/grid toggle on desktop.
- One date control for both panes: "‹ Saturday, Sep 26 ›" centered above them, plus a "Pick a date" button that opens a two-month calendar. The list only shows the selected day.
- Filters apply to both panes.
- The grid shows every rink in the rink filter side by side, with fixed-width sheet columns. It scrolls sideways when they don't fit, with a visible scrollbar, and the hour labels stay fixed.
- Map pin card: Directions (Google Maps), Website, and View schedule.
- Preferences opens narrow with just the filters; the arrow on the Rinks row expands it to show a small map and one rink list (sorted by distance) for starring. Reset and Save span the whole dialog.

## Known drift

- The dimmed page behind the Preferences dialog is the older list + map Schedule layout, not the current one.
- Renton's grid columns are empty; the sample data only has Kraken and Kirkland sessions.
- The date picker's per-day session counts are placeholders except Sat 26 and Sun 27, and it assumes schedules are posted through Oct 9.
