import type { JSX } from "preact";

import type { Rink } from "../data";

/**
 * Schedule tab placeholder until the list (#12) and grid (#13) land.
 * @param rinks Rinks from `rinks.json`.
 */
export function ScheduleView({ rinks }: { rinks: Rink[] }): JSX.Element {
  return (
    <section class="placeholder">
      <h1>Schedule</h1>
      <p>List and grid views are coming. {rinks.length} rinks loaded.</p>
    </section>
  );
}
