import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from searinks.daysmart.parse import parse_events
from searinks.daysmart.source import DaySmartSource
from searinks.models.event import Event
from searinks.models.rink import Rink

PACIFIC = ZoneInfo("America/Los_Angeles")

RINK = Rink(
    key="test",
    name="Test Rink",
    timezone="America/Los_Angeles",
    source=DaySmartSource(
        company="testco",
        sheets={1: "Sheet 1", 2: "Sheet 2"},
        drop_in_program_types=frozenset({"Camp", "Drop-In"}),
        discipline_overrides={"UW Club Hockey 26-27": "figure", "SAS 26-27": "hockey"},
    ),
)

PROGRAMS = [
    {"type": "sports", "id": "20", "attributes": {"name": "Hockey"}},
    {"type": "sports", "id": "31", "attributes": {"name": "Open Freestyle"}},
    {"type": "sports", "id": "40", "attributes": {"name": "Private Lessons"}},
    {"type": "program-types", "id": "1", "attributes": {"name": "Camp"}},
    {"type": "program-types", "id": "2", "attributes": {"name": "Class"}},
    {"type": "program-types", "id": "3", "attributes": {"name": "Drop-In"}},
    {"type": "program-types", "id": "4", "attributes": {"name": "Per-session Class"}},
]

EVENT_TYPES = [
    {"type": "event-types", "id": "k", "attributes": {"name": "Camp"}},
    {"type": "event-types", "id": "r", "attributes": {"name": "Rental"}},
]


def _event(
    event_id: str,
    *,
    resource_id: int = 1,
    desc: str = "",
    event_type_id: str = "k",
    publish: bool = True,
    start: str = "2026-09-26T12:45:00",
    end: str = "2026-09-26T14:15:00",
    hteam_id: int | None = None,
) -> dict[str, Any]:
    """Build a JSON:API event resource.

    Args:
        event_id: Event id, also used as the summary id.
        resource_id: DaySmart resource (ice sheet) id.
        desc: Raw event description.
        event_type_id: DaySmart event type code.
        publish: Whether the event is published.
        start: Local start timestamp.
        end: Local end timestamp.
        hteam_id: Id of the program ("team") the event belongs to.
    """
    return {
        "type": "events",
        "id": event_id,
        "attributes": {
            "resource_id": resource_id,
            "desc": desc,
            "event_type_id": event_type_id,
            "publish": publish,
            "start": start,
            "end": end,
            "hteam_id": hteam_id,
        },
        "relationships": {
            "summary": {"data": {"type": "event-summaries", "id": event_id}},
            "eventType": {"data": {"type": "event-types", "id": event_type_id}},
        },
    }


def _summary(event_id: str, name: str, open_slots: int = 10, capacity: int = 20) -> dict[str, Any]:
    """Build a JSON:API event-summary resource.

    Args:
        event_id: Id of the event this summarizes.
        name: Display name DaySmart shows for the event.
        open_slots: Remaining registration slots.
        capacity: Total registration capacity.
    """
    return {
        "type": "event-summaries",
        "id": event_id,
        "attributes": {"name": name, "open_slots": open_slots, "composite_capacity": capacity},
    }


def _team(team_id: int, sport_id: str, program_type_id: str) -> dict[str, Any]:
    """Build a JSON:API team (program) resource.

    Args:
        team_id: Team id referenced by an event's `hteam_id`.
        sport_id: Id of the team's sport.
        program_type_id: Id of the team's program type.
    """
    return {
        "type": "teams",
        "id": str(team_id),
        "attributes": {},
        "relationships": {
            "sport": {"data": {"type": "sports", "id": sport_id}},
            "programType": {"data": {"type": "program-types", "id": program_type_id}},
        },
    }


def _page(
    data: list[dict[str, Any]], included: list[dict[str, Any]], current: int = 1, last: int = 1
) -> dict[str, Any]:
    """Build a paginated JSON:API response body.

    Args:
        data: Primary event resources.
        included: Sideloaded resources.
        current: Current page number.
        last: Last page number.
    """
    return {
        "meta": {"page": {"current-page": current, "last-page": last}},
        "data": data,
        "included": included,
    }


def test_parse_events_reads_event_fields() -> None:
    # GIVEN: a public skate with a summary name and an empty raw desc
    body = _page([_event("1", resource_id=2)], [_summary("1", "Public Skate Saturdays", 296, 300), *EVENT_TYPES])

    # WHEN: parsing the page
    events = parse_events(body, RINK)

    # THEN: the event carries its rink, localized times, sheet name, type, capacity and discipline
    assert events == [
        Event(
            id="1",
            title="Public Skate Saturdays",
            event_type="Camp",
            rink="test",
            sheet="Sheet 2",
            start=datetime(2026, 9, 26, 12, 45, tzinfo=PACIFIC),
            end=datetime(2026, 9, 26, 14, 15, tzinfo=PACIFIC),
            open_slots=296,
            capacity=300,
            discipline="public",
        )
    ]


@pytest.mark.parametrize(
    ("program", "sport", "drop_in"),
    [
        (_team(7, sport_id="20", program_type_id="1"), "Hockey", True),
        (_team(7, sport_id="31", program_type_id="2"), "Open Freestyle", False),
        (_team(7, sport_id="40", program_type_id="1"), "Private Lessons", False),
        (_team(7, sport_id="20", program_type_id="3"), "Hockey", True),
        (_team(7, sport_id="20", program_type_id="4"), "Hockey", False),
        (None, None, False),
    ],
)
def test_parse_events_reads_sport_and_drop_in_from_program(
    program: dict[str, Any] | None, sport: str | None, drop_in: bool
) -> None:
    # GIVEN: an event linked to the given program, or to none (e.g. a rental)
    included = [_summary("1", "Thing"), *EVENT_TYPES, *PROGRAMS, *([program] if program else [])]
    body = _page([_event("1", hteam_id=7 if program else None)], included)

    # WHEN: parsing the page
    (parsed,) = parse_events(body, RINK)

    # THEN: sport comes from the program and only the rink's drop-in program types count
    assert parsed.sport == sport
    assert parsed.drop_in is drop_in


@pytest.mark.parametrize(
    ("summary_name", "desc", "expected"),
    [
        ("Stick & Puck", "", "Stick & Puck"),
        ("", "UW Club Hockey 26-27", "UW Club Hockey 26-27"),
        ("  ", "  SAS 26-27 ", "SAS 26-27"),
    ],
)
def test_parse_events_title_prefers_summary_name_then_desc(summary_name: str, desc: str, expected: str) -> None:
    # GIVEN: an event with the given summary name and raw desc
    body = _page([_event("1", desc=desc)], [_summary("1", summary_name), *EVENT_TYPES])

    # WHEN: parsing the page
    (parsed,) = parse_events(body, RINK)

    # THEN: the title falls back from summary name to desc
    assert parsed.title == expected


@pytest.mark.parametrize(
    ("resource_id", "publish", "kept"),
    [
        (1, True, True),
        (1, False, False),
        (99, True, False),
    ],
)
def test_parse_events_keeps_only_published_events_on_ice_sheets(resource_id: int, publish: bool, kept: bool) -> None:
    # GIVEN: an event on the given resource with the given publish flag
    body = _page([_event("1", resource_id=resource_id, publish=publish)], [_summary("1", "Thing"), *EVENT_TYPES])

    # WHEN: parsing the page
    events = parse_events(body, RINK)

    # THEN: only published events on configured sheets survive
    assert (len(events) == 1) is kept


@pytest.mark.parametrize(
    ("desc", "discipline"),
    [
        ("SAS 26-27", "hockey"),
        ("UW Club Hockey 26-27", "figure"),
        ("Aspire Freestyle", "figure"),
        ("Birthday Party", None),
    ],
)
def test_parse_events_resolves_discipline_with_rink_overrides(desc: str, discipline: str | None) -> None:
    # GIVEN: an event with no program at a rink that overrides two titles, one against its keywords
    body = _page([_event("1", desc=desc)], [_summary("1", ""), *EVENT_TYPES])

    # WHEN: parsing the page
    (parsed,) = parse_events(body, RINK)

    # THEN: the rink's override applies, and other titles fall back to the shared keywords
    assert parsed.discipline == discipline


def test_parse_events_logs_nothing_for_expected_events(caplog: pytest.LogCaptureFixture) -> None:
    # GIVEN: a program event, a rental with no program and an event off the ice sheets
    body = _page(
        [_event("1", hteam_id=7), _event("2", event_type_id="r"), _event("3", resource_id=9)],
        [_summary("1", "Stick & Puck"), _summary("2", "Rental"), *EVENT_TYPES, *PROGRAMS, _team(7, "20", "1")],
    )
    caplog.set_level(logging.DEBUG)

    # WHEN: parsing the page
    parse_events(body, RINK)

    # THEN: nothing is logged
    assert caplog.records == []


@pytest.mark.parametrize(
    ("event", "included", "message"),
    [
        (_event("1", hteam_id=7), [_summary("1", "Thing"), *EVENT_TYPES, *PROGRAMS], "daysmart_program_missing"),
        (
            _event("1", hteam_id=7),
            [_summary("1", "Thing"), *EVENT_TYPES, *PROGRAMS, _team(7, sport_id="99", program_type_id="1")],
            "daysmart_program_incomplete",
        ),
        (_event("1", event_type_id="zz"), [_summary("1", "Thing"), *EVENT_TYPES], "daysmart_event_type_missing"),
        (_event("1", desc=" "), [_summary("1", ""), *EVENT_TYPES], "daysmart_event_untitled"),
    ],
)
def test_parse_events_warns_on_unexpected_events(
    caplog: pytest.LogCaptureFixture, event: dict[str, Any], included: list[dict[str, Any]], message: str
) -> None:
    # GIVEN: an event whose program, event type or name can't be resolved
    caplog.set_level(logging.WARNING)

    # WHEN: parsing the page
    events = parse_events(_page([event], included), RINK)

    # THEN: the event is kept and one warning names the rink and event
    assert len(events) == 1
    (record,) = caplog.records
    assert (record.levelname, record.message, record.rink, record.event_id) == ("WARNING", message, "test", "1")


def test_parse_events_skips_and_warns_on_malformed_events(caplog: pytest.LogCaptureFixture) -> None:
    # GIVEN: an event missing its start time, next to a good one
    malformed = _event("1")
    del malformed["attributes"]["start"]
    body = _page([malformed, _event("2")], [_summary("1", "Thing"), _summary("2", "Thing"), *EVENT_TYPES])
    caplog.set_level(logging.WARNING)

    # WHEN: parsing the page
    events = parse_events(body, RINK)

    # THEN: the malformed event is dropped with a warning and the good one is kept
    assert [e.id for e in events] == ["2"]
    (record,) = caplog.records
    assert (record.message, record.rink, record.event_id) == ("daysmart_event_malformed", "test", "1")
    assert "start" in record.error
