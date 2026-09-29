import { describe, expect, it } from "vitest";

import { Button } from "@/components/Button";

describe("Button", () => {
  it.each([
    [undefined, "btn"],
    ["primary", "btn btn-primary"],
    ["text", "btn btn-text"],
  ] as const)("renders variant %s with class %j", (variant, expected) => {
    // WHEN: rendering a button with the given variant
    const vnode = Button({ variant, children: "Go" });

    // THEN: it gets the shared base class plus its variant's
    expect(vnode.props.class).toBe(expected);
  });

  it("appends the caller's class after the shared ones", () => {
    // WHEN: rendering a button with an extra class
    const vnode = Button({ variant: "primary", class: "sheet-done", children: "Done" });

    // THEN: the caller's class comes last so it can refine the variant
    expect(vnode.props.class).toBe("btn btn-primary sheet-done");
  });

  it("defaults to type=button but lets callers override it", () => {
    // GIVEN: one button with no type and one submit button
    const plain = Button({ children: "Go" });
    const submit = Button({ type: "submit", children: "Save" });

    // THEN: buttons don't submit forms unless asked to
    expect(plain.props.type).toBe("button");
    expect(submit.props.type).toBe("submit");
  });

  it("passes other props through", () => {
    // GIVEN: an onClick handler and an aria-label
    const onClick = (): void => {};

    // WHEN: rendering a button with them
    const vnode = Button({ onClick, "aria-label": "Close", children: "x" });

    // THEN: both land on the <button>
    expect(vnode.type).toBe("button");
    expect(vnode.props.onClick).toBe(onClick);
    expect(vnode.props["aria-label"]).toBe("Close");
  });
});
