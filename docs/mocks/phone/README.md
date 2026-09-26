# Phone mocks (D2)

Finalized phone UI for the web frontend (tracking issue #17). Open any file in a browser; the tabs and gear link between screens. Sample data is Sat Sep 26, 2026.

Source canvas: https://claude.ai/artifact/VsbPzaAqoaoC8YgT4qfUgd (top row; the theme explorations below it are not final). These files are static exports of that row; update both together.

| Screen | File | Ticket |
|--------|------|--------|
| Schedule, list view | [schedule-list.html](schedule-list.html) | #12 |
| Schedule, grid view (one rink's day, sheets side by side) | [schedule-grid.html](schedule-grid.html) | #13 |
| Map and starred rinks | [map.html](map.html) | #14 |
| Preferences | [preferences.html](preferences.html) | #15 |

## Design tokens

| Token | Value |
|-------|-------|
| Display font | Baloo 2 (500-800) |
| Body font | DM Sans (500-800) |
| Ink | `#12284A` |
| Muted text | `#56677D` |
| Accent | `#1F4FCC` |
| Page background | `#F4F9FD` |
| Header band | `#E4EFFB` |
| Divider | `#DCE8F3` |
| Neutral chip | `#E7EFF7` |
| Hockey tag | bg `#DCE7FF`, text `#1B3FA8` |
| Figure tag | bg `#F1E2FF`, text `#5B2A91` |
| Public tag | bg `#D6F4F1`, text `#0B5C57` |
| Nearly full capacity | `#A34A0B` |
| Current-time line (grid) | `#E5484D` |

## Decisions

- Tabs: Schedule (list/grid toggle) and Map; the gear opens Preferences.
- Favorites are starred on the Map; the rink filter defaults to starred rinks, or all rinks if none are starred.
- Filters: a filter icon plus only the selected filters as small chips.
- Capacity shows as taken/total.
- The app always opens with the Preferences defaults.
- Never show which data source a rink comes from.

## Known drift

- Olympic View and Lynnwood show as "coming soon" on the Map; both are connected now.
