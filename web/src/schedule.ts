// Pure helpers for the schedule views: dates, filtering and display text.

import type { Event, Rink } from "@/data";

export type Discipline = NonNullable<Event["discipline"]>;

export type Filters = {
  /** Disciplines to keep; empty keeps every event. */
  sports: Discipline[];
  dropIn: boolean;
};

export type Capacity = { taken: number; total: number; state: "open" | "nearly" | "full" };

const TIME_ZONE = "America/Los_Angeles";
const NEARLY_FULL = 0.9;

const ISO_DATE = new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" });
const HEADING = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", weekday: "long", month: "short", day: "numeric" });
const TIME = new Intl.DateTimeFormat("en-US", { timeZone: TIME_ZONE, hour: "numeric", minute: "2-digit", hourCycle: "h23" });

/**
 * Today's date in Seattle as YYYY-MM-DD.
 * @param now Current instant; injectable for tests.
 */
export function todayPacific(now: Date = new Date()): string {
  return ISO_DATE.format(now);
}

/**
 * Parse a YYYY-MM-DD date as midnight UTC, so date math ignores the viewer's timezone.
 * @param date Date as YYYY-MM-DD.
 */
function utcDate(date: string): Date {
  return new Date(`${date}T00:00:00Z`);
}

/**
 * Consecutive dates starting on `start`.
 * @param start First date as YYYY-MM-DD.
 * @param count Number of dates.
 */
export function weekDates(start: string, count: number): string[] {
  const first = utcDate(start).getTime();
  return Array.from({ length: count }, (_, i) => new Date(first + i * 86_400_000).toISOString().slice(0, 10));
}

/**
 * Day heading like "Saturday, Sep 26".
 * @param date Date as YYYY-MM-DD.
 */
export function dayHeading(date: string): string {
  return HEADING.format(utcDate(date));
}

/**
 * Weekday and day-of-month parts for the date strip, e.g. ["Sat", "26"].
 * @param date Date as YYYY-MM-DD.
 */
export function stripLabel(date: string): [string, string] {
  const d = utcDate(date);
  return [d.toLocaleDateString("en-US", { timeZone: "UTC", weekday: "short" }), String(d.getUTCDate())];
}

/**
 * 24-hour Pacific time like "6:00" or "20:45".
 * @param iso ISO timestamp with offset.
 */
export function formatTime(iso: string): string {
  const parts = Object.fromEntries(TIME.formatToParts(new Date(iso)).map((p) => [p.type, p.value]));
  return `${Number(parts.hour)}:${parts.minute}`;
}

/**
 * Keep the events that match the sport and drop-in filters.
 * @param events Events to filter.
 * @param filters Selected filters.
 */
export function filterEvents(events: Event[], filters: Filters): Event[] {
  return events.filter(
    (e) =>
      (filters.sports.length === 0 || (e.discipline !== null && filters.sports.includes(e.discipline))) &&
      (!filters.dropIn || e.drop_in),
  );
}

/**
 * Taken/total for an event, or null when its source doesn't report both.
 * @param event Event to describe.
 */
export function capacity(event: Event): Capacity | null {
  if (event.capacity === null || event.open_slots === null || event.capacity <= 0) return null;
  const taken = event.capacity - event.open_slots;
  const state = event.open_slots <= 0 ? "full" : taken / event.capacity >= NEARLY_FULL ? "nearly" : "open";
  return { taken, total: event.capacity, state };
}

/**
 * "Rink · Sheet", or just the rink when it has one sheet.
 * @param event Event to describe.
 * @param rink The event's rink.
 */
export function rinkLine(event: Event, rink: Rink): string {
  return rink.sheets.length > 1 ? `${rink.name} · ${event.sheet}` : rink.name;
}

/**
 * Short names of the selected rinks in rink order, e.g. "Kraken & Kirkland".
 * @param rinks Every rink, in display order.
 * @param selected Selected rink keys; empty means all.
 */
export function rinksLabel(rinks: Rink[], selected: string[]): string {
  const names = rinks.filter((r) => selected.includes(r.key)).map((r) => r.short_name);
  if (names.length === 0 || names.length === rinks.length) return "All rinks";
  if (names.length === 1) return names[0];
  return `${names.slice(0, -1).join(", ")} & ${names[names.length - 1]}`;
}

/**
 * What to say under a day heading when there's nothing to list, or null when there are events to show.
 * @param counts.events Events across the day's rinks, before filtering.
 * @param counts.shown Events left after filtering.
 */
export function dayMessage(counts: { events: number; shown: number }): string | null {
  if (counts.shown > 0) return null;
  return counts.events === 0 ? "No events" : "No events match your filters";
}
