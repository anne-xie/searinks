import { toChildArray, type VNode } from "preact";
import { describe, expect, it } from "vitest";

import { SessionCard } from "@/components/SessionCard";
import type { Event, Rink } from "@/data";

const RINK = { key: "kraken", name: "Kraken Community Iceplex", sheets: ["Starbucks Rink 1"] } as Rink;
const URL = "https://example.test/book";

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
    open_slots: 0,
    capacity: 34,
    sport: null,
    drop_in: true,
    discipline: "hockey",
    ...overrides,
  };
}

/**
 * Classes of the card's direct children.
 * @param card Rendered card.
 */
function childClasses(card: VNode<any>): string[] {
  return toChildArray(card.props.children).map((child) => (child as VNode<any>).props.class);
}

describe("SessionCard", () => {
  it("offers Book on a full session that has a booking link", () => {
    // GIVEN: a full session with a booking link
    const card = SessionCard({ event: event({ booking_url: URL }), rink: RINK });

    // THEN: it's marked full but can still be booked, since the count may be stale
    expect(card.props.class).toBe("card card-full");
    expect(childClasses(card)).toEqual(["card-times", "card-body", "card-book"]);
  });

  it("shows Full in place of Book when a full session has no link", () => {
    // GIVEN: a full session without a booking link
    const card = SessionCard({ event: event(), rink: RINK });

    // THEN: the status fills the Book slot
    expect(childClasses(card)).toEqual(["card-times", "card-body", "card-status"]);
  });
});
