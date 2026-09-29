import type { JSX } from "preact";

import "@/components/Button.css";

export type ButtonVariant = "primary" | "text";

/**
 * A <button> with the shared reset and focus ring; `type` defaults to "button".
 * @param variant Filled accent ("primary"), accent-colored text ("text"), or unstyled.
 * @param class Extra classes, applied after the shared ones.
 * @param props Any other <button> attributes.
 */
export function Button({
  variant,
  class: extra,
  ...props
}: { variant?: ButtonVariant } & JSX.ButtonHTMLAttributes<HTMLButtonElement>): JSX.Element {
  const classes = ["btn", variant && `btn-${variant}`, extra].filter(Boolean).join(" ");
  return <button type="button" {...props} class={classes} />;
}
