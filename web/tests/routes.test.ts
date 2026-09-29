import { describe, expect, it } from "vitest";

import { parseRoute } from "@/routes";

describe("parseRoute", () => {
  it.each([
    ["#/schedule", "schedule"],
    ["#/map", "map"],
    ["#/preferences", "preferences"],
    ["", "schedule"],
    ["#/nope", "schedule"],
  ])("maps %j to %s", (hash, expected) => {
    // WHEN/THEN: known hashes pick their view and anything else falls back to the schedule
    expect(parseRoute(hash)).toBe(expected);
  });
});
