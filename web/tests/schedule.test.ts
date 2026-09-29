import { describe, expect, it } from "vitest";

import type { Event, Rink } from "@/data";
import {
  capacity,
  dayHeading,
  dayMessage,
  filterEvents,
  formatTime,
  rinkLine,
  rinksLabel,
  todayPacific,
  weekDates,
} from "@/schedule";

/**
 * Build an event with sensible defaults.
 * @param overrides Fields to change.
 */
function event(overrides: Partial<Event> = {}): Event {
  return {
    id: "1",
    title: "Stick & Puck",
    rink: "kraken",
    sheet: "Starbucks Rink 1",
    start: "2026-09-26T11:15:00-07:00",
    end: "2026-09-26T12:15:00-07:00",
    event_type: null,
    open_slots: 15,
    capacity: 34,
    sport: null,
    drop_in: true,
    discipline: "hockey",
    ...overrides,
  };
}

/**
 * Build a rink with the given key, short name and sheets.
 * @param key Rink key.
 * @param shortName Short display name.
 * @param sheets Sheet names.
 */
function rink(key: string, shortName: string, sheets: string[] = ["Main Rink"]): Rink {
  return { key, name: `${shortName} Arena`, short_name: shortName, code: "XXX", area: "Seattle", lat: 0, lng: 0, sheets };
}

describe("todayPacific", () => {
  it.each([
    ["2026-09-29T06:30:00Z", "2026-09-28"],
    ["2026-09-29T07:30:00Z", "2026-09-29"],
  ])("maps %s to %s", (instant, expected) => {
    // WHEN/THEN: the date is the one in Seattle, not UTC
    expect(todayPacific(new Date(instant))).toBe(expected);
  });
});

describe("weekDates", () => {
  it("lists consecutive days across a month boundary", () => {
    // WHEN/THEN: seven days start on the given date
    expect(weekDates("2026-09-28", 7)).toEqual([
      "2026-09-28",
      "2026-09-29",
      "2026-09-30",
      "2026-10-01",
      "2026-10-02",
      "2026-10-03",
      "2026-10-04",
    ]);
  });
});

describe("dayHeading", () => {
  it("names the weekday, month and day", () => {
    // WHEN/THEN: the heading matches the mocks
    expect(dayHeading("2026-09-26")).toBe("Saturday, Sep 26");
  });
});

describe("formatTime", () => {
  it.each([
    ["2026-09-26T06:00:00-07:00", "6:00"],
    ["2026-09-26T20:45:00-07:00", "20:45"],
    ["2026-09-26T13:00:00Z", "6:00"],
  ])("formats %s as %s", (iso, expected) => {
    // WHEN/THEN: times are 24-hour, Pacific, without a leading zero
    expect(formatTime(iso)).toBe(expected);
  });
});

describe("filterEvents", () => {
  const hockeyDropIn = event({ id: "a" });
  const hockeySeries = event({ id: "b", drop_in: false });
  const figure = event({ id: "c", discipline: "figure" });
  const unknown = event({ id: "d", discipline: null });
  const all = [hockeyDropIn, hockeySeries, figure, unknown];

  it.each([
    [{ sports: [], dropIn: false }, ["a", "b", "c", "d"]],
    [{ sports: ["hockey"], dropIn: false }, ["a", "b"]],
    [{ sports: ["hockey", "figure"], dropIn: false }, ["a", "b", "c"]],
    [{ sports: ["hockey"], dropIn: true }, ["a"]],
    [{ sports: [], dropIn: true }, ["a", "c", "d"]],
  ] as const)("with %j keeps %j", (filters, expected) => {
    // WHEN/THEN: no sports means every sport, and drop-in narrows to per-session events
    expect(filterEvents(all, { sports: [...filters.sports], dropIn: filters.dropIn }).map((e) => e.id)).toEqual(
      expected,
    );
  });
});

describe("capacity", () => {
  it.each([
    [{ open_slots: 15, capacity: 34 }, { taken: 19, total: 34, state: "open" }],
    [{ open_slots: 1, capacity: 20 }, { taken: 19, total: 20, state: "nearly" }],
    [{ open_slots: 0, capacity: 20 }, { taken: 20, total: 20, state: "full" }],
    [{ open_slots: 34, capacity: 34 }, { taken: 0, total: 34, state: "open" }],
    [{ open_slots: null, capacity: 34 }, null],
    [{ open_slots: 3, capacity: null }, null],
    [{ open_slots: 0, capacity: 0 }, null],
  ])("for %j is %j", (slots, expected) => {
    // WHEN/THEN: taken/total with full at no slots left and nearly full at 90% taken
    expect(capacity(event(slots))).toEqual(expected);
  });
});

describe("rinkLine", () => {
  it.each([
    [rink("kraken", "Kraken", ["Rink 1", "Rink 2"]), "Kraken Arena · Starbucks Rink 1"],
    [rink("kirkland", "Kirkland", ["Kirkland"]), "Kirkland Arena"],
  ])("for %j is %s", (r, expected) => {
    // WHEN/THEN: the sheet is only named when the rink has more than one
    expect(rinkLine(event(), r)).toBe(expected);
  });
});

describe("rinksLabel", () => {
  const rinks = [rink("kraken", "Kraken"), rink("kirkland", "Kirkland"), rink("renton", "Renton")];

  it.each([
    [["kraken"], "Kraken"],
    [["kraken", "kirkland"], "Kraken & Kirkland"],
    [["renton", "kraken"], "Kraken & Renton"],
    [["kraken", "kirkland", "renton"], "All rinks"],
    [[], "All rinks"],
  ])("for %j is %s", (selected, expected) => {
    // WHEN/THEN: short names in rink order, and every rink (or none picked) reads as all rinks
    expect(rinksLabel(rinks, selected)).toBe(expected);
  });

  it("lists three or more with commas", () => {
    // GIVEN: four rinks, three of them selected
    const four = [...rinks, rink("ova", "Olympic View")];

    // WHEN/THEN: commas with an ampersand before the last
    expect(rinksLabel(four, ["kraken", "kirkland", "ova"])).toBe("Kraken, Kirkland & Olympic View");
  });
});

describe("dayMessage", () => {
  it.each([
    [{ events: 3, shown: 2 }, null],
    [{ events: 0, shown: 0 }, "No events"],
    [{ events: 3, shown: 0 }, "No events match your filters"],
  ])("for %j is %j", (counts, expected) => {
    // WHEN/THEN: a day with nothing scheduled says so, and filtered-out events are told apart
    expect(dayMessage(counts)).toBe(expected);
  });
});
