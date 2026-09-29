import { useEffect, useState } from "preact/hooks";

import { type Day, type Event, loadDay } from "@/data";

export type LoadedDay = {
  date: string;
  /** Events across the requested rinks, sorted by start then rink; a rink-day that wasn't exported adds none. */
  events: Event[];
};

// One request per rink-day for the life of the page; failed requests are dropped so they can retry.
const cache = new Map<string, Promise<Day | null>>();

/**
 * Load one rink-day through the cache.
 * @param date Day as YYYY-MM-DD.
 * @param rink Rink key.
 */
function cachedDay(date: string, rink: string): Promise<Day | null> {
  const key = `${date}/${rink}`;
  let day = cache.get(key);
  if (!day) {
    day = loadDay(date, rink);
    cache.set(key, day);
    day.catch(() => cache.delete(key));
  }
  return day;
}

/**
 * Load every requested rink for every requested day.
 * @param dates Days as YYYY-MM-DD.
 * @param rinks Rink keys.
 * @returns Days in order once all have loaded (null while loading), whether any request failed,
 *   and each loaded file's `generated_at`.
 */
export function useDays(
  dates: string[],
  rinks: string[],
): { days: LoadedDay[] | null; error: boolean; generatedAt: string[] } {
  const [state, setState] = useState<{ days: LoadedDay[] | null; error: boolean; generatedAt: string[] }>({
    days: null,
    error: false,
    generatedAt: [],
  });
  const key = `${dates.join(",")}|${rinks.join(",")}`;

  useEffect(() => {
    let current = true;
    setState((s) => ({ ...s, days: null, error: false }));
    Promise.all(dates.map((date) => Promise.all(rinks.map((rink) => cachedDay(date, rink))))).then(
      (perDate) => {
        if (!current) return;
        const generatedAt: string[] = [];
        const days = perDate.map((files, i) => {
          const events = files.flatMap((file) => file?.events ?? []);
          files.forEach((file) => file && generatedAt.push(file.generated_at));
          events.sort((a, b) => Date.parse(a.start) - Date.parse(b.start) || a.rink.localeCompare(b.rink));
          return { date: dates[i], events };
        });
        setState({ days, error: false, generatedAt });
      },
      () => current && setState({ days: null, error: true, generatedAt: [] }),
    );
    return () => {
      current = false;
    };
  }, [key]);

  return state;
}
