from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.daysmart.source import DaySmartSource
from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rectimes.source import RecTimesSource
from searinks.rinks.registry import RINKS
from searinks.schedule import get_all_schedules, get_schedule

PACIFIC = ZoneInfo("America/Los_Angeles")


def _rink(key: str, source: DaySmartSource | RecTimesSource | None = None) -> Rink:
    """Build a rink with one sheet.

    Args:
        key: Rink key, also used as the DaySmart company.
        source: Schedule source; defaults to DaySmart.
    """
    return Rink(
        key=key,
        name=key.title(),
        timezone="America/Los_Angeles",
        source=source
        or DaySmartSource(company=key, sheets={1: "Sheet 1"}, drop_in_program_types=frozenset({"Camp"})),
    )


RINK_A = _rink("alpha")
RINK_B = _rink("bravo")
RINK_RECTIMES = _rink("charlie", RecTimesSource(facility="charlie", venues={1: "Sheet 1"}, drop_in_groups=frozenset()))


def _event(
    event_id: str,
    title: str,
    discipline: str | None = None,
    drop_in: bool = False,
    rink: str = "alpha",
    hour: int = 12,
) -> Event:
    """Build an event on Sheet 1.

    Args:
        event_id: Event id.
        title: Event title.
        discipline: Resolved discipline.
        drop_in: Whether the event is sold per session.
        rink: Key of the rink the event belongs to.
        hour: Start hour on 2026-09-26.
    """
    start = datetime(2026, 9, 26, hour, tzinfo=PACIFIC)
    return Event(
        id=event_id,
        title=title,
        rink=rink,
        sheet="Sheet 1",
        start=start,
        end=start,
        drop_in=drop_in,
        discipline=discipline,
    )


EVENTS = [
    _event("stick", "Stick & Puck", "hockey", drop_in=True),
    _event("public", "Public Skate Saturdays", "public", drop_in=True),
    _event("freestyle", "Open Freestyle | Pre-Paid", "figure"),
    _event("game", "Seattle Slapshots vs Seal Team Sticks", "hockey"),
    _event("rental", "Birthday Party"),
]


@pytest.fixture
def client_cls() -> MagicMock:
    """Patch the DaySmart client class used by `get_schedule`, serving `EVENTS` for every rink."""
    with patch("searinks.schedule.DaySmartClient") as cls:
        cls.return_value.get_events.return_value = EVENTS
        yield cls


def test_get_schedule_fetches_each_rink_for_the_date_range(client_cls: MagicMock) -> None:
    # WHEN: asking for two rinks over a date range
    get_schedule([RINK_A, RINK_B], date(2026, 9, 26), date(2026, 9, 28))

    # THEN: each rink gets its own client, queried for that range
    assert sorted(c.args[0].key for c in client_cls.call_args_list) == ["alpha", "bravo"]
    assert client_cls.return_value.get_events.call_count == 2
    client_cls.return_value.get_events.assert_called_with(date(2026, 9, 26), date(2026, 9, 28))


@patch("searinks.schedule.RecTimesClient")
@patch("searinks.schedule.DaySmartClient")
def test_get_schedule_picks_client_from_rink_source(daysmart_cls: MagicMock, rectimes_cls: MagicMock) -> None:
    # GIVEN: a DaySmart rink and a RecTimes rink, each client serving one event
    daysmart_cls.return_value.get_events.return_value = [_event("d", "DaySmart", rink="alpha")]
    rectimes_cls.return_value.get_events.return_value = [_event("r", "RecTimes", rink="charlie")]

    # WHEN: fetching both rinks
    events = get_schedule([RINK_A, RINK_RECTIMES], date(2026, 9, 26), date(2026, 9, 26))

    # THEN: each rink is fetched by the client matching its source
    daysmart_cls.assert_called_once_with(RINK_A)
    rectimes_cls.assert_called_once_with(RINK_RECTIMES)
    assert sorted(e.id for e in events) == ["d", "r"]


@patch("searinks.schedule.DaySmartClient")
def test_get_schedule_merges_rinks_sorted_by_start_then_rink(client_cls: MagicMock) -> None:
    # GIVEN: each rink returns events interleaved in time with the other's
    per_rink = {
        "alpha": [_event("a9", "A 9am", rink="alpha", hour=9), _event("a12", "A noon", rink="alpha", hour=12)],
        "bravo": [_event("b8", "B 8am", rink="bravo", hour=8), _event("b12", "B noon", rink="bravo", hour=12)],
    }
    client_cls.side_effect = lambda rink: MagicMock(get_events=MagicMock(return_value=per_rink[rink.key]))

    # WHEN: fetching both rinks
    events = get_schedule([RINK_B, RINK_A], date(2026, 9, 26), date(2026, 9, 26))

    # THEN: results are merged and ordered by start time, ties broken by rink
    assert [e.id for e in events] == ["b8", "a9", "a12", "b12"]


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
def test_get_schedule_applies_filters(client_cls: MagicMock, filters: dict, expected_ids: list[str]) -> None:
    # WHEN: fetching one rink with the given filters
    events = get_schedule([RINK_A], date(2026, 9, 26), date(2026, 9, 26), **filters)

    # THEN: only matching events are returned
    assert sorted(e.id for e in events) == sorted(expected_ids)


@patch("searinks.schedule.get_schedule", return_value=EVENTS)
def test_get_all_schedules_queries_every_registered_rink_with_filters(get_schedule_mock: MagicMock) -> None:
    # WHEN: fetching every rink with filters
    events = get_all_schedules(date(2026, 9, 26), date(2026, 9, 27), search="stick", drop_in=True, sport="hockey")

    # THEN: get_schedule runs once over all registered rinks with the same range and filters
    get_schedule_mock.assert_called_once_with(
        list(RINKS.values()), date(2026, 9, 26), date(2026, 9, 27), search="stick", drop_in=True, sport="hockey"
    )
    assert events == EVENTS
