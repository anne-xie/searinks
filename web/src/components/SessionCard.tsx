import type { JSX } from "preact";

import type { Event, Rink } from "@/data";
import { bookingUrl, capacity, formatTime, rinkLine } from "@/schedule";

const SPORT_LABELS = { hockey: "Hockey", figure: "Figure", public: "Public" } as const;

/**
 * One session in the list: times, title, where, sport, taken/total and a Book link when it can be booked.
 * @param event Session to show.
 * @param rink The session's rink.
 */
export function SessionCard({ event, rink }: { event: Event; rink: Rink }): JSX.Element {
  const cap = capacity(event);
  const full = cap?.state === "full";
  const bookUrl = bookingUrl(event);
  return (
    <article class={full ? "card card-full" : "card"}>
      <div class="card-times">
        <span class="card-start">{formatTime(event.start)}</span>
        <span class="card-end">{formatTime(event.end)}</span>
      </div>
      <div class="card-body">
        <div class="card-title">{event.title}</div>
        <div class="card-where">{rinkLine(event, rink)}</div>
        <div class="card-meta">
          {event.discipline && <span class={`tag tag-${event.discipline}`}>{SPORT_LABELS[event.discipline]}</span>}
          {cap && (
            <span class={cap.state === "nearly" ? "capacity-nearly" : undefined}>
              {cap.taken}/{cap.total}
              {full && " · Full"}
            </span>
          )}
        </div>
      </div>
      {full && <span class="card-status">Full</span>}
      {bookUrl && (
        <a class="card-book" href={bookUrl} target="_blank" rel="noopener" aria-label={`Book ${event.title}`}>
          Book
        </a>
      )}
    </article>
  );
}
