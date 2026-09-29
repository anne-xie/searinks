import type { JSX } from "preact";

import { stripLabel } from "@/schedule";

/**
 * Row of days; the selected one is filled.
 * @param dates Days as YYYY-MM-DD.
 * @param selected Day to highlight.
 * @param onSelect Called with the tapped day.
 */
export function DateStrip({
  dates,
  selected,
  onSelect,
}: {
  dates: string[];
  selected: string;
  onSelect: (date: string) => void;
}): JSX.Element {
  return (
    <div class="strip">
      {dates.map((date) => {
        const [weekday, day] = stripLabel(date);
        return (
          <button
            key={date}
            type="button"
            class="strip-day"
            aria-label={`Jump to ${weekday} ${day}`}
            aria-current={date === selected ? "date" : undefined}
            onClick={() => onSelect(date)}
          >
            <span class="strip-weekday">{weekday}</span>
            <span class="strip-number">{day}</span>
          </button>
        );
      })}
    </div>
  );
}
