import type { JSX } from "preact";

import { Button } from "@/components/Button";
import { CloseIcon } from "@/components/icons";
import type { Discipline } from "@/schedule";
import "@/components/Chip.css";

type ChipProps = { label: string; discipline?: Discipline } & (
  | { pressed?: never; onToggle?: never; onRemove?: never; removeLabel?: never }
  | { pressed: boolean; onToggle: () => void; onRemove?: never; removeLabel?: never }
  | { pressed?: never; onToggle?: never; onRemove: () => void; removeLabel: string }
);

/**
 * Rounded label in its discipline's colors: static, an on/off toggle, or removable.
 * @param label Text shown.
 * @param discipline Picks the colors; omitted uses the neutral selected colors.
 * @param pressed With `onToggle`, whether the toggle is on. Off toggles are grey.
 * @param onToggle Makes the chip a toggle button.
 * @param onRemove Adds a remove button after the label.
 * @param removeLabel Accessible name for the remove button.
 */
export function Chip({ label, discipline, pressed, onToggle, onRemove, removeLabel }: ChipProps): JSX.Element {
  const color = discipline ? ` chip-${discipline}` : "";
  if (onToggle) {
    return (
      <Button class={`chip chip-toggle${color}`} aria-pressed={pressed} onClick={onToggle}>
        {label}
      </Button>
    );
  }
  if (onRemove) {
    return (
      <span class={`chip chip-removable${color}`}>
        {label}
        <Button class="chip-remove" aria-label={removeLabel} onClick={onRemove}>
          <CloseIcon />
        </Button>
      </span>
    );
  }
  return <span class={`chip chip-static${color}`}>{label}</span>;
}
