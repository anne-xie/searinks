import type { JSX } from "preact";

import type { Rink } from "@/data";

/**
 * Map tab placeholder until #14 lands.
 * @param rinks Rinks from `rinks.json`.
 */
export function MapView({ rinks }: { rinks: Rink[] }): JSX.Element {
  return (
    <section class="placeholder">
      <h1>Map</h1>
      <ul class="rink-list">
        {rinks.map((rink) => (
          <li key={rink.key}>
            <span class="rink-name">{rink.name}</span>
            <span class="muted">
              {rink.area} · {rink.sheets.length} {rink.sheets.length === 1 ? "sheet" : "sheets"}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
