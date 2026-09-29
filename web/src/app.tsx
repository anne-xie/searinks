import type { JSX } from "preact";
import { useEffect, useState } from "preact/hooks";

import { Header } from "@/components/Header";
import { lastUpdated, loadRinks, type RinksFile } from "@/data";
import { useRoute } from "@/routes";
import { MapView } from "@/views/MapView";
import { PreferencesView } from "@/views/PreferencesView";
import { ScheduleView } from "@/views/ScheduleView";

const UPDATED_FORMAT = new Intl.DateTimeFormat("en-US", {
  weekday: "short",
  hour: "numeric",
  minute: "2-digit",
  timeZone: "America/Los_Angeles",
});

/** App shell: header, the current view and when the data was last exported. */
export function App(): JSX.Element {
  const route = useRoute();
  const [rinks, setRinks] = useState<RinksFile | null>(null);
  const [error, setError] = useState(false);
  const [dayTimestamps, setDayTimestamps] = useState<string[]>([]);

  useEffect(() => {
    loadRinks().then(setRinks, () => setError(true));
  }, []);

  const updated = rinks && lastUpdated([rinks.generated_at, ...dayTimestamps]);

  return (
    <div class="app">
      <Header route={route} />
      <main class="main">
        {error ? (
          <p class="notice">Couldn't load rink data. Try again in a bit.</p>
        ) : !rinks ? (
          <p class="notice">Loading…</p>
        ) : route === "map" ? (
          <MapView rinks={rinks.rinks} />
        ) : route === "preferences" ? (
          <PreferencesView />
        ) : (
          <ScheduleView rinks={rinks.rinks} onLoaded={setDayTimestamps} />
        )}
      </main>
      {updated && <footer class="updated">Updated {UPDATED_FORMAT.format(new Date(updated))}</footer>}
    </div>
  );
}
