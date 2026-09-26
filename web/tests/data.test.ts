import { afterEach, describe, expect, it, vi } from "vitest";

import { type Day, lastUpdated, loadDay, loadRinks, type RinksFile } from "../src/data";

const RINKS: RinksFile = {
  generated_at: "2026-09-26T08:00:00-07:00",
  rinks: [
    {
      key: "kraken",
      name: "Kraken Community Iceplex",
      short_name: "Kraken",
      code: "KCI",
      area: "Northgate",
      lat: 47.7063,
      lng: -122.3252,
      sheets: ["Starbucks Rink 1"],
    },
  ],
};

const DAY: Day = { date: "2026-09-26", rink: "kraken", generated_at: "2026-09-26T08:00:00-07:00", events: [] };

/**
 * Stub `fetch` with one response.
 * @param status HTTP status to answer with.
 * @param body JSON body to answer with.
 */
function stubFetch(status: number, body: unknown = {}): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("loadRinks", () => {
  it("fetches rinks.json from the data folder", async () => {
    // GIVEN: the export's rink list is available
    const fetchMock = stubFetch(200, RINKS);

    // WHEN: loading rinks
    const result = await loadRinks();

    // THEN: the file is read from data/ under the site base and returned as is
    expect(fetchMock).toHaveBeenCalledWith("/data/rinks.json");
    expect(result).toEqual(RINKS);
  });

  it("throws when the rink list can't be read", async () => {
    // GIVEN: the rink list is missing
    stubFetch(404);

    // WHEN/THEN: loading fails loudly, since nothing works without rinks
    await expect(loadRinks()).rejects.toThrow("rinks.json: 404");
  });
});

describe("loadDay", () => {
  it("fetches one rink's day file", async () => {
    // GIVEN: the day was exported
    const fetchMock = stubFetch(200, DAY);

    // WHEN: loading that day
    const result = await loadDay("2026-09-26", "kraken");

    // THEN: the per-day, per-rink file is read and returned
    expect(fetchMock).toHaveBeenCalledWith("/data/days/2026-09-26/kraken.json");
    expect(result).toEqual(DAY);
  });

  it("returns null when the day wasn't exported", async () => {
    // GIVEN: no file for that day and rink
    stubFetch(404);

    // WHEN: loading that day
    const result = await loadDay("2026-10-30", "kraken");

    // THEN: the day is reported as unavailable rather than empty
    expect(result).toBeNull();
  });

  it("throws on other errors", async () => {
    // GIVEN: the server fails
    stubFetch(500);

    // WHEN/THEN: the failure surfaces instead of looking like a missing day
    await expect(loadDay("2026-09-26", "kraken")).rejects.toThrow("days/2026-09-26/kraken.json: 500");
  });
});

describe("lastUpdated", () => {
  it.each([
    [[], null],
    [["2026-09-26T08:00:00-07:00"], "2026-09-26T08:00:00-07:00"],
    [["2026-09-26T09:00:00-07:00", "2026-09-26T15:30:00Z", "2026-09-26T10:00:00-07:00"], "2026-09-26T15:30:00Z"],
  ])("returns the oldest of %j", (timestamps, expected) => {
    // WHEN/THEN: the oldest instant wins, comparing across offsets
    expect(lastUpdated(timestamps)).toBe(expected);
  });
});
