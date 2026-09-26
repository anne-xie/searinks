from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from searinks.filters import filter_events
from searinks.models.event import Event

PACIFIC = ZoneInfo("America/Los_Angeles")


def _event(event_id: str, title: str, discipline: str | None = None, drop_in: bool = False, hour: int = 12) -> Event:
    """Build an event on Sheet 1.

    Args:
        event_id: Event id.
        title: Event title.
        discipline: Resolved discipline.
        drop_in: Whether the event is sold per session.
        hour: Start hour on 2026-09-26.
    """
    start = datetime(2026, 9, 26, hour, tzinfo=PACIFIC)
    return Event(
        id=event_id,
        title=title,
        rink="alpha",
        sheet="Sheet 1",
        start=start,
        end=start,
        drop_in=drop_in,
        discipline=discipline,
    )


EVENTS = [
    _event("stick", "Stick & Puck", "hockey", drop_in=True, hour=8),
    _event("public", "Public Skate Saturdays", "public", drop_in=True, hour=9),
    _event("freestyle", "Open Freestyle | Pre-Paid", "figure", hour=10),
    _event("game", "Seattle Slapshots vs Seal Team Sticks", "hockey", hour=11),
    _event("rental", "Birthday Party", hour=12),
]


@pytest.mark.parametrize(
    ("filters", "expected_ids"),
    [
        ({}, ["stick", "public", "freestyle", "game", "rental"]),
        ({"search": "PUBLIC skate"}, ["public"]),
        ({"search": "stick"}, ["stick", "game"]),
        ({"drop_in": True}, ["stick", "public"]),
        ({"sport": "hockey"}, ["stick", "game"]),
        ({"sport": "figure"}, ["freestyle"]),
        ({"drop_in": True, "sport": "hockey"}, ["stick"]),
        ({"drop_in": True, "search": "stick"}, ["stick"]),
    ],
)
def test_filter_events_keeps_matching_events_in_order(filters: dict, expected_ids: list[str]) -> None:
    # WHEN: filtering events sorted by start time
    events = filter_events(EVENTS, **filters)

    # THEN: only matching events remain, in their original order
    assert [e.id for e in events] == expected_ids
