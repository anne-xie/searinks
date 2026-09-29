import logging
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.daysmart.source import DaySmartSource
from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rectimes.source import RecTimesSource
from searinks.rinks.registry import RINKS
from searinks.schedule import get_all_schedules, get_schedule, tenant_groups

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
        short_name=key.title(),
        code=key[:3].upper(),
        area="Seattle",
        lat=47.6,
        lng=-122.3,
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


def test_get_schedule_fetches_each_tenant_for_the_date_range(client_cls: MagicMock) -> None:
    # WHEN: asking for two rinks on different companies over a date range
    get_schedule([RINK_A, RINK_B], date(2026, 9, 26), date(2026, 9, 28))

    # THEN: each company gets its own client, queried for that range
    assert sorted(c.args[0][0].key for c in client_cls.call_args_list) == ["alpha", "bravo"]
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
    daysmart_cls.assert_called_once_with([RINK_A])
    rectimes_cls.assert_called_once_with([RINK_RECTIMES])
    assert sorted(e.id for e in events) == ["d", "r"]


@patch("searinks.schedule.DaySmartClient")
def test_get_schedule_merges_rinks_sorted_by_start_then_rink(client_cls: MagicMock) -> None:
    # GIVEN: each rink returns events interleaved in time with the other's
    per_rink = {
        "alpha": [_event("a9", "A 9am", rink="alpha", hour=9), _event("a12", "A noon", rink="alpha", hour=12)],
        "bravo": [_event("b8", "B 8am", rink="bravo", hour=8), _event("b12", "B noon", rink="bravo", hour=12)],
    }
    client_cls.side_effect = lambda rinks: MagicMock(get_events=MagicMock(return_value=per_rink[rinks[0].key]))

    # WHEN: fetching both rinks
    events = get_schedule([RINK_B, RINK_A], date(2026, 9, 26), date(2026, 9, 26))

    # THEN: results are merged and ordered by start time, ties broken by rink
    assert [e.id for e in events] == ["b8", "a9", "a12", "b12"]


SHARED_A = _rink("kirk", DaySmartSource(company="shared", sheets={1: "A"}, drop_in_program_types=frozenset()))
SHARED_B = _rink("ren", DaySmartSource(company="shared", sheets={2: "B"}, drop_in_program_types=frozenset()))
SHARED_C = _rink("snq", DaySmartSource(company="shared", sheets={3: "C"}, drop_in_program_types=frozenset()))
FACILITY_A = _rink("ova", RecTimesSource(facility="shared", venues={1: "A"}, drop_in_groups=frozenset()))
FACILITY_B = _rink("lyn", RecTimesSource(facility="shared", venues={2: "B"}, drop_in_groups=frozenset()))


@pytest.mark.parametrize(
    ("rinks", "expected"),
    [
        ([RINK_A, RINK_B], [["alpha"], ["bravo"]]),
        ([SHARED_A, RINK_A, SHARED_B], [["kirk", "ren"], ["alpha"]]),
        ([FACILITY_A, SHARED_A, FACILITY_B], [["ova", "lyn"], ["kirk"]]),
    ],
)
def test_tenant_groups_groups_rinks_by_source_account(rinks: list[Rink], expected: list[list[str]]) -> None:
    # WHEN/THEN: rinks on the same DaySmart company or RecTimes facility share a group, in first-seen order,
    # and a DaySmart company never groups with a RecTimes facility of the same name
    assert [[rink.key for rink in group] for group in tenant_groups(rinks)] == expected


def test_get_schedule_fetches_a_shared_company_once(client_cls: MagicMock) -> None:
    # WHEN: asking for three rinks on the same company
    get_schedule([SHARED_A, SHARED_B, SHARED_C], date(2026, 9, 26), date(2026, 9, 26))

    # THEN: one client serves all three, so the company's API is called once
    client_cls.assert_called_once_with([SHARED_A, SHARED_B, SHARED_C])
    client_cls.return_value.get_events.assert_called_once()


@patch("searinks.schedule.RecTimesClient")
def test_get_schedule_logs_overrides_missing_from_results(
    rectimes_cls: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    # GIVEN: a rink overriding two titles, only one of which is on its schedule
    rink = _rink(
        "delta",
        RecTimesSource(
            facility="delta",
            venues={1: "Sheet 1"},
            drop_in_groups=frozenset(),
            discipline_overrides={"SJHA": "hockey", "OVHL": "hockey"},
        ),
    )
    rectimes_cls.return_value.get_events.return_value = [_event("s", "SJHA", "hockey", rink="delta")]
    caplog.set_level(logging.DEBUG)

    # WHEN: fetching the rink
    get_schedule([rink], date(2026, 9, 26), date(2026, 9, 26))

    # THEN: only the override that matched nothing is logged, at debug level
    assert [(r.levelname, r.message, r.rink, r.title) for r in caplog.records] == [
        ("DEBUG", "discipline_override_unmatched", "delta", "OVHL")
    ]


@patch("searinks.schedule.get_schedule", return_value=EVENTS)
def test_get_all_schedules_queries_every_registered_rink(get_schedule_mock: MagicMock) -> None:
    # WHEN: fetching every rink
    events = get_all_schedules(date(2026, 9, 26), date(2026, 9, 27))

    # THEN: get_schedule runs once over all registered rinks with the same range
    get_schedule_mock.assert_called_once_with(list(RINKS.values()), date(2026, 9, 26), date(2026, 9, 27))
    assert events == EVENTS
