from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest

from searinks.daysmart import DaySmartClient, Event, discipline_for
from searinks.rinks import RINKS, Rink

PACIFIC = ZoneInfo("America/Los_Angeles")

RINK = Rink(
    key="test",
    name="Test Rink",
    company="testco",
    timezone="America/Los_Angeles",
    sheets={1: "Sheet 1", 2: "Sheet 2"},
)


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


PROGRAMS = [
    {"type": "sports", "id": "20", "attributes": {"name": "Hockey"}},
    {"type": "sports", "id": "31", "attributes": {"name": "Open Freestyle"}},
    {"type": "sports", "id": "40", "attributes": {"name": "Private Lessons"}},
    {"type": "program-types", "id": "1", "attributes": {"name": "Camp"}},
    {"type": "program-types", "id": "2", "attributes": {"name": "Class"}},
]

EVENT_TYPES = [
    {"type": "event-types", "id": "k", "attributes": {"name": "Camp"}},
    {"type": "event-types", "id": "r", "attributes": {"name": "Rental"}},
]


def _page(data: list[dict[str, Any]], included: list[dict[str, Any]], current: int, last: int) -> dict[str, Any]:
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


def _client(pages: dict[int, dict[str, Any]], requests: list[httpx.Request]) -> DaySmartClient:
    """Build a client whose HTTP layer serves canned pages keyed by page number.

    Args:
        pages: Response body per `page[number]`.
        requests: List that captured requests are appended to.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=pages[int(request.url.params["page[number]"])])

    return DaySmartClient(RINK, http=httpx.Client(transport=httpx.MockTransport(handler)))


def test_get_events_sends_company_and_date_filters() -> None:
    # GIVEN: a single empty page
    requests: list[httpx.Request] = []
    client = _client({1: _page([], [], 1, 1)}, requests)

    # WHEN: fetching a date range
    client.get_events(date(2026, 9, 26), date(2026, 9, 27))

    # THEN: the request is scoped to the rink's company and date range
    params = requests[0].url.params
    assert requests[0].url.path == "/dash/jsonapi/api/v1/events"
    assert params["company"] == "testco"
    assert params["filter[start_date__gte]"] == "2026-09-26"
    assert params["filter[start_date__lte]"] == "2026-09-27"


def test_get_events_parses_event_fields() -> None:
    # GIVEN: a public skate with a summary name and an empty raw desc
    included = [_summary("1", "Public Skate Saturdays", open_slots=296, capacity=300), *EVENT_TYPES]
    client = _client({1: _page([_event("1", resource_id=2)], included, 1, 1)}, [])

    # WHEN: fetching events
    events = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: the event carries localized times, sheet name, type and capacity
    assert events == [
        Event(
            id="1",
            title="Public Skate Saturdays",
            event_type="Camp",
            sheet="Sheet 2",
            start=datetime(2026, 9, 26, 12, 45, tzinfo=PACIFIC),
            end=datetime(2026, 9, 26, 14, 15, tzinfo=PACIFIC),
            open_slots=296,
            capacity=300,
        )
    ]


@pytest.mark.parametrize(
    ("team", "sport", "drop_in"),
    [
        (_team(7, sport_id="20", program_type_id="1"), "Hockey", True),
        (_team(7, sport_id="31", program_type_id="2"), "Open Freestyle", False),
        (_team(7, sport_id="40", program_type_id="1"), "Private Lessons", False),
        (None, None, False),
    ],
)
def test_get_events_reads_sport_and_drop_in_from_program(
    team: dict[str, Any] | None, sport: str | None, drop_in: bool
) -> None:
    # GIVEN: an event linked to the given program, or to none (e.g. a rental)
    included = [_summary("1", "Thing"), *EVENT_TYPES, *PROGRAMS, *([team] if team else [])]
    client = _client({1: _page([_event("1", hteam_id=7 if team else None)], included, 1, 1)}, [])

    # WHEN: fetching events
    (event,) = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: sport comes from the program and only per-session Camp programs count as drop-in
    assert event.sport == sport
    assert event.drop_in is drop_in


@pytest.mark.parametrize(
    ("sport", "expected"),
    [
        ("Hockey", "hockey"),
        ("Open Freestyle", "figure"),
        ("FS Club Freestyle", "figure"),
        ("FS Group Classes", "figure"),
        ("Ice Dance", "figure"),
        ("Public Skate", "public"),
        ("Learn to Skate", None),
        (None, None),
    ],
)
def test_discipline_for_groups_sport_names(sport: str | None, expected: str | None) -> None:
    # WHEN/THEN: DaySmart sport names map to a coarse discipline
    assert discipline_for(sport) == expected


@pytest.mark.parametrize(
    ("summary_name", "desc", "expected"),
    [
        ("Stick & Puck", "", "Stick & Puck"),
        ("", "UW Club Hockey 26-27", "UW Club Hockey 26-27"),
        ("  ", "  SAS 26-27 ", "SAS 26-27"),
    ],
)
def test_title_prefers_summary_name_then_desc(summary_name: str, desc: str, expected: str) -> None:
    # GIVEN: an event with the given summary name and raw desc
    included = [_summary("1", summary_name), *EVENT_TYPES]
    client = _client({1: _page([_event("1", desc=desc)], included, 1, 1)}, [])

    # WHEN: fetching events
    (event,) = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: the title falls back from summary name to desc
    assert event.title == expected


@pytest.mark.parametrize(
    ("resource_id", "publish", "kept"),
    [
        (1, True, True),
        (1, False, False),
        (99, True, False),
    ],
)
def test_get_events_keeps_only_published_events_on_ice_sheets(resource_id: int, publish: bool, kept: bool) -> None:
    # GIVEN: an event on the given resource with the given publish flag
    included = [_summary("1", "Thing"), *EVENT_TYPES]
    client = _client({1: _page([_event("1", resource_id=resource_id, publish=publish)], included, 1, 1)}, [])

    # WHEN: fetching events
    events = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: only published events on configured sheets survive
    assert (len(events) == 1) is kept


def test_get_events_follows_pagination_and_sorts_by_start() -> None:
    # GIVEN: two pages, with the later event on the first page
    page1 = _page([_event("2", start="2026-09-26T18:00:00")], [_summary("2", "Late"), *EVENT_TYPES], 1, 2)
    page2 = _page([_event("1", start="2026-09-26T06:00:00")], [_summary("1", "Early"), *EVENT_TYPES], 2, 2)
    requests: list[httpx.Request] = []
    client = _client({1: page1, 2: page2}, requests)

    # WHEN: fetching events
    events = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: both pages are requested and results are sorted by start time
    assert len(requests) == 2
    assert [e.title for e in events] == ["Early", "Late"]


def test_kraken_rink_is_registered() -> None:
    # GIVEN/WHEN: looking up the Kraken Community Iceplex
    rink = RINKS["kraken"]

    # THEN: it points at the kraken DaySmart tenant and its three NHL sheets
    assert rink.company == "kraken"
    assert set(rink.sheets) == {1, 2, 3}
