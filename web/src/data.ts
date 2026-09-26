// Reads the static JSON written by `searinks-export` (see src/searinks/export.py).

export type Rink = {
  key: string;
  name: string;
  short_name: string;
  code: string;
  area: string;
  lat: number;
  lng: number;
  sheets: string[];
};

export type RinksFile = {
  generated_at: string;
  rinks: Rink[];
};

export type Event = {
  id: string;
  title: string;
  rink: string;
  sheet: string;
  start: string;
  end: string;
  event_type: string | null;
  open_slots: number | null;
  capacity: number | null;
  sport: string | null;
  drop_in: boolean;
  discipline: "hockey" | "figure" | "public" | null;
};

export type Day = {
  date: string;
  rink: string;
  generated_at: string;
  events: Event[];
};

/**
 * Fetch a file from the export's `data/` folder under the site base.
 * @param path Path inside `data/`.
 */
function fetchData(path: string): Promise<Response> {
  return fetch(`${import.meta.env.BASE_URL}data/${path}`);
}

/** Load the rink list; throws if it can't be read, since every view needs it. */
export async function loadRinks(): Promise<RinksFile> {
  const response = await fetchData("rinks.json");
  if (!response.ok) throw new Error(`rinks.json: ${response.status}`);
  return response.json();
}

/**
 * Load one rink's events for one day.
 * @param date Day as YYYY-MM-DD.
 * @param rink Rink key.
 * @returns The day, or null when that day wasn't exported for the rink.
 */
export async function loadDay(date: string, rink: string): Promise<Day | null> {
  const path = `days/${date}/${rink}.json`;
  const response = await fetchData(path);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  return response.json();
}

/**
 * Pick the timestamp to show as "last updated": the oldest of the loaded files.
 * @param timestamps ISO timestamps from each file's `generated_at`.
 */
export function lastUpdated(timestamps: string[]): string | null {
  if (timestamps.length === 0) return null;
  return timestamps.reduce((oldest, t) => (Date.parse(t) < Date.parse(oldest) ? t : oldest));
}
