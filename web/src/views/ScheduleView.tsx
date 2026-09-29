import type { JSX } from "preact";
import { useEffect, useMemo, useRef, useState } from "preact/hooks";

import { DateStrip } from "@/components/DateStrip";
import { SPORTS, FilterSheet } from "@/components/FilterSheet";
import { CloseIcon, FilterIcon, PinIcon } from "@/components/icons";
import { SessionCard } from "@/components/SessionCard";
import type { Rink } from "@/data";
import { DEFAULT_PREFERENCES, type Preferences } from "@/preferences";
import { dayHeading, dayMessage, filterEvents, rinksLabel, todayPacific, weekDates } from "@/schedule";
import { type LoadedDay, useDays } from "@/useDays";
import "@/views/ScheduleView.css";

const DAYS = 7;

/**
 * Schedule tab, list layout: a week of sessions across the selected rinks.
 * @param rinks Every rink from `rinks.json`.
 * @param onLoaded Called with the `generated_at` of every day file shown.
 */
export function ScheduleView({
  rinks,
  onLoaded,
}: {
  rinks: Rink[];
  onLoaded: (generatedAt: string[]) => void;
}): JSX.Element {
  const dates = useMemo(() => weekDates(todayPacific(), DAYS), []);
  const [filters, setFilters] = useState<Preferences>(DEFAULT_PREFERENCES);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [selected, setSelected] = useState(dates[0]);

  const rinkKeys = filters.rinks.length ? rinks.filter((r) => filters.rinks.includes(r.key)).map((r) => r.key) : rinks.map((r) => r.key);
  const { days, error, generatedAt } = useDays(dates, rinkKeys);
  useEffect(() => onLoaded(generatedAt), [generatedAt]);

  const sticky = useRef<HTMLDivElement>(null);
  const headings = useRef(new Map<string, HTMLElement>());

  // Highlight the day whose heading was last scrolled past the sticky date strip.
  useEffect(() => {
    const onScroll = (): void => {
      const top = (sticky.current?.getBoundingClientRect().bottom ?? 0) + 12;
      let current = dates[0];
      for (const date of dates) {
        const el = headings.current.get(date);
        if (el && el.getBoundingClientRect().top <= top) current = date;
      }
      setSelected(current);
    };
    addEventListener("scroll", onScroll, { passive: true });
    return () => removeEventListener("scroll", onScroll);
  }, [dates]);

  const jumpTo = (date: string): void => {
    const el = headings.current.get(date);
    if (!el) return;
    const offset = sticky.current?.getBoundingClientRect().height ?? 0;
    scrollTo({ top: el.getBoundingClientRect().top + scrollY - offset - 8, behavior: "smooth" });
    setSelected(date);
  };

  const byKey = new Map(rinks.map((r) => [r.key, r]));
  const chips = [
    ...(filters.dropIn ? [{ label: "Drop-in", remove: () => setFilters((f) => ({ ...f, dropIn: false })) }] : []),
    ...SPORTS.filter((s) => filters.sports.includes(s.key)).map((s) => ({
      label: s.label,
      remove: () => setFilters((f) => ({ ...f, sports: f.sports.filter((k) => k !== s.key) })),
    })),
  ];

  return (
    <section class="schedule">
      <div class="schedule-sticky" ref={sticky}>
        <DateStrip dates={dates} selected={selected} onSelect={jumpTo} />
      </div>

      <div class="filter-row">
        <button
          type="button"
          class="filter-button"
          aria-label={`Filters, ${chips.length} selected`}
          onClick={() => setSheetOpen(true)}
        >
          <FilterIcon />
          {chips.length > 0 && <span class="filter-badge">{chips.length}</span>}
        </button>
        {chips.map((chip) => (
          <span key={chip.label} class="chip">
            {chip.label}
            <button type="button" class="chip-remove" aria-label={`Remove ${chip.label} filter`} onClick={chip.remove}>
              <CloseIcon />
            </button>
          </span>
        ))}
      </div>

      <div class="showing">
        <span class="showing-pin">
          <PinIcon />
        </span>
        <span>
          Showing <strong>{rinksLabel(rinks, filters.rinks)}</strong>
        </span>
        <button type="button" class="showing-change" onClick={() => setSheetOpen(true)}>
          Change
        </button>
      </div>

      {error ? (
        <p class="notice">Couldn't load the schedule. Try again in a bit.</p>
      ) : !days ? (
        <p class="notice">Loading…</p>
      ) : (
        days.map((day) => (
          <DaySection
            key={day.date}
            day={day}
            filters={filters}
            byKey={byKey}
            headingRef={(el) => (el ? headings.current.set(day.date, el) : headings.current.delete(day.date))}
          />
        ))
      )}

      <FilterSheet
        open={sheetOpen}
        filters={filters}
        rinks={rinks}
        onChange={setFilters}
        onClose={() => setSheetOpen(false)}
      />
    </section>
  );
}

/**
 * One day's heading and sessions, or a note when there are none.
 * @param day Loaded events for the day.
 * @param filters Current filters.
 * @param byKey Rinks by key.
 * @param headingRef Receives the heading element, for scroll tracking.
 */
function DaySection({
  day,
  filters,
  byKey,
  headingRef,
}: {
  day: LoadedDay;
  filters: Preferences;
  byKey: Map<string, Rink>;
  headingRef: (el: HTMLElement | null) => void;
}): JSX.Element {
  const events = filterEvents(day.events, filters);
  const message = dayMessage({ events: day.events.length, shown: events.length });

  return (
    <div class="day">
      <h2 class="day-heading" ref={headingRef}>
        {dayHeading(day.date)}
      </h2>
      {message ? (
        <p class="day-empty">{message}</p>
      ) : (
        <div class="cards">
          {events.map((event) => {
            const rink = byKey.get(event.rink);
            return rink && <SessionCard key={`${event.rink}/${event.id}`} event={event} rink={rink} />;
          })}
        </div>
      )}
    </div>
  );
}
