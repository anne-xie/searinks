import type { VNode } from "preact";
import { describe, expect, it } from "vitest";

import { Button } from "@/components/Button";
import { Chip } from "@/components/Chip";

describe("Chip", () => {
  it.each([
    [undefined, "chip chip-static"],
    ["hockey", "chip chip-static chip-hockey"],
    ["figure", "chip chip-static chip-figure"],
    ["public", "chip chip-static chip-public"],
  ] as const)("colors a static chip for discipline %s", (discipline, expected) => {
    // WHEN: rendering a label-only chip
    const vnode = Chip({ label: "Figure", discipline });

    // THEN: it's a span with the discipline's color class, if any
    expect(vnode.type).toBe("span");
    expect(vnode.props.class).toBe(expected);
    expect(vnode.props.children).toBe("Figure");
  });

  it.each([true, false])("renders a toggle chip with aria-pressed=%s", (pressed) => {
    // GIVEN: a toggle handler
    const onToggle = (): void => {};

    // WHEN: rendering a toggle chip
    const vnode = Chip({ label: "Public", discipline: "public", pressed, onToggle });

    // THEN: it's a shared Button that reports its state and calls the handler
    expect(vnode.type).toBe(Button);
    expect(vnode.props.class).toBe("chip chip-toggle chip-public");
    expect(vnode.props["aria-pressed"]).toBe(pressed);
    expect(vnode.props.onClick).toBe(onToggle);
  });

  it("renders a removable chip with a labeled remove button", () => {
    // GIVEN: a remove handler
    const onRemove = (): void => {};

    // WHEN: rendering a removable chip
    const vnode = Chip({ label: "Hockey", discipline: "hockey", onRemove, removeLabel: "Remove Hockey filter" });

    // THEN: the label sits beside a Button that removes it
    const [label, remove] = vnode.props.children as [string, VNode<Record<string, unknown>>];
    expect(vnode.type).toBe("span");
    expect(vnode.props.class).toBe("chip chip-removable chip-hockey");
    expect(label).toBe("Hockey");
    expect(remove.type).toBe(Button);
    expect(remove.props.class).toBe("chip-remove");
    expect(remove.props["aria-label"]).toBe("Remove Hockey filter");
    expect(remove.props.onClick).toBe(onRemove);
  });
});
