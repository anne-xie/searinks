from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.schedule import get_schedule

PACIFIC = ZoneInfo("America/Los_Angeles")

RINK = Rink(
    key="test",
    name="Test Rink",
    company="testco",
    timezone="America/Los_Angeles",
    sheets={1: "Sheet 1"},
    drop_in_program_types=frozenset({"Camp"}),
)


def _event(event_id: str, title: str, sport: str | None, drop_in: bool) -> Event:
    """Build an event on Sheet 1.

    Args:
        event_id: Event id.
        title: Event title.
        sport: Program sport name.
        drop_in: Whether the event is sold per session.
    """
    start = datetime(2026, 9, 26, 12, tzinfo=PACIFIC)
    return Event(
        id=event_id, title=title, event_type="Camp", sheet="Sheet 1", start=start, end=start, sport=sport, drop_in=drop_in
    )


EVENTS = [
    _event("stick", "Stick & Puck", "Hockey", drop_in=True),
    _event("public", "Public Skate Saturdays", "Public Skate", drop_in=True),
    _event("freestyle", "Open Freestyle | Pre-Paid", "Open Freestyle", drop_in=False),
    _event("game", "Seattle Slapshots vs Seal Team Sticks", "Hockey", drop_in=False),
]


@pytest.fixture
def client() -> MagicMock:
    """Patch the DaySmart client used by `get_schedule` and return the instance mock."""
    with patch("searinks.schedule.DaySmartClient") as cls:
        cls.return_value.get_events.return_value = EVENTS
        yield cls.return_value


@patch("searinks.schedule.DaySmartClient")
def test_get_schedule_fetches_rink_and_date_range(client_cls: MagicMock) -> None:
    # GIVEN: a client with no events
    client_cls.return_value.get_events.return_value = []

    # WHEN: asking for a date range
    get_schedule(RINK, date(2026, 9, 26), date(2026, 9, 28))

    # THEN: the rink's client is queried for that range
    client_cls.assert_called_once_with(RINK)
    client_cls.return_value.get_events.assert_called_once_with(date(2026, 9, 26), date(2026, 9, 28))


@pytest.mark.parametrize(
    ("filters", "expected_ids"),
    [
        ({}, ["stick", "public", "freestyle", "game"]),
        ({"search": "PUBLIC skate"}, ["public"]),
        ({"search": "stick"}, ["stick", "game"]),
        ({"drop_in": True}, ["stick", "public"]),
        ({"sport": "hockey"}, ["stick", "game"]),
        ({"sport": "figure"}, ["freestyle"]),
        ({"drop_in": True, "sport": "hockey"}, ["stick"]),
        ({"drop_in": True, "search": "stick"}, ["stick"]),
    ],
)
def test_get_schedule_applies_filters(client: MagicMock, filters: dict, expected_ids: list[str]) -> None:
    # WHEN: fetching with the given filters
    events = get_schedule(RINK, date(2026, 9, 26), date(2026, 9, 26), **filters)

    # THEN: only matching events are returned, in their original order
    assert [e.id for e in events] == expected_ids
