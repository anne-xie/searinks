import type { JSX } from "preact";
import { useEffect, useRef } from "preact/hooks";

import type { Rink } from "@/data";
import type { Preferences } from "@/preferences";
import type { Discipline } from "@/schedule";
import "@/components/FilterSheet.css";

export const SPORTS: { key: Discipline; label: string }[] = [
  { key: "hockey", label: "Hockey" },
  { key: "figure", label: "Figure" },
  { key: "public", label: "Public" },
];

/**
 * Add or remove a value from a list.
 * @param list Current values.
 * @param value Value to toggle.
 */
function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

/**
 * Bottom sheet with every filter; changes apply as they're made.
 * @param open Whether the sheet is showing.
 * @param filters Current filters.
 * @param rinks Every rink, in display order.
 * @param onChange Called with a function from the current filters to the updated ones.
 * @param onClose Called when the sheet is dismissed.
 */
export function FilterSheet({
  open,
  filters,
  rinks,
  onChange,
  onClose,
}: {
  open: boolean;
  filters: Preferences;
  rinks: Rink[];
  onChange: (update: (filters: Preferences) => Preferences) => void;
  onClose: () => void;
}): JSX.Element {
  const dialog = useRef<HTMLDialogElement>(null);
  // Hide the element right away rather than after the list re-renders, then report it.
  const close = (): void => {
    dialog.current?.close();
    onClose();
  };

  useEffect(() => {
    const el = dialog.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  // Esc closes the dialog natively; keep `open` in step.
  useEffect(() => {
    const el = dialog.current;
    el?.addEventListener("close", onClose);
    return () => el?.removeEventListener("close", onClose);
  }, [onClose]);

  return (
    <dialog
      ref={dialog}
      class="sheet"
      aria-labelledby="filters-title"
      onClick={(e) => e.target === dialog.current && close()}
    >
      <div class="sheet-body">
        <h2 id="filters-title" class="sheet-title">
          Filters
        </h2>

        <label class="sheet-row">
          <span class="sheet-label">Drop-in only</span>
          <input
            type="checkbox"
            role="switch"
            class="switch"
            checked={filters.dropIn}
            onChange={() => onChange((f) => ({ ...f, dropIn: !f.dropIn }))}
          />
        </label>

        <fieldset class="sheet-group">
          <legend class="sheet-label">Sports</legend>
          <div class="chips">
            {SPORTS.map((sport) => (
              <button
                key={sport.key}
                type="button"
                class="chip-toggle"
                aria-pressed={filters.sports.includes(sport.key)}
                onClick={() => onChange((f) => ({ ...f, sports: toggle(f.sports, sport.key) }))}
              >
                {sport.label}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset class="sheet-group">
          <legend class="sheet-label">Rinks</legend>
          {rinks.map((rink) => (
            <label key={rink.key} class="sheet-check">
              <input
                type="checkbox"
                checked={filters.rinks.includes(rink.key)}
                onChange={() => onChange((f) => ({ ...f, rinks: toggle(f.rinks, rink.key) }))}
              />
              <span>{rink.name}</span>
            </label>
          ))}
          <p class="sheet-hint">None checked shows every rink.</p>
        </fieldset>

        <button type="button" class="sheet-done" onClick={close}>
          Done
        </button>
      </div>
    </dialog>
  );
}
