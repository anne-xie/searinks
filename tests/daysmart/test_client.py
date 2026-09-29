from dataclasses import replace
from datetime import date, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import httpx

from searinks.daysmart.client import DaySmartClient
from searinks.daysmart.source import DaySmartSource
from searinks.models.event import Event
from searinks.models.rink import Rink

RINK = Rink(
    key="test",
    name="Test Rink",
    short_name="Test",
    code="TST",
    area="Seattle",
    lat=47.6,
    lng=-122.3,
    timezone="America/Los_Angeles",
    source=DaySmartSource(company="testco", sheets={1: "Sheet 1"}, drop_in_program_types=frozenset({"Camp"})),
)


SIBLING = replace(
    RINK,
    key="sibling",
    source=DaySmartSource(company="testco", sheets={2: "Sheet 2"}, drop_in_program_types=frozenset({"Camp"})),
)


def _client(last_page: int, requests: list[httpx.Request], rinks: list[Rink] | None = None) -> DaySmartClient:
    """Build a client whose HTTP layer returns bodies tagged with their page number.

    Args:
        last_page: `last-page` reported in every response.
        requests: List that captured requests are appended to.
        rinks: Rinks the client serves; defaults to `RINK` alone.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body: dict[str, Any] = {"page": request.url.params["page[number]"], "meta": {"page": {"last-page": last_page}}}
        return httpx.Response(200, json=body)

    return DaySmartClient(rinks or [RINK], http=httpx.Client(transport=httpx.MockTransport(handler)))


def _event(title: str, hour: int, rink: str = "test") -> Event:
    """Build an event starting at the given hour.

    Args:
        title: Event title.
        hour: Start hour on 2026-09-26.
        rink: Key of the rink the event is at.
    """
    start = datetime(2026, 9, 26, hour)
    return Event(id=title, title=title, event_type="Camp", rink=rink, sheet="Sheet 1", start=start, end=start)


@patch("searinks.daysmart.client.parse_events", return_value=[])
def test_get_events_sends_company_and_date_filters(parse_events: MagicMock) -> None:
    # GIVEN: a single page
    requests: list[httpx.Request] = []
    client = _client(last_page=1, requests=requests)

    # WHEN: fetching a date range
    client.get_events(date(2026, 9, 26), date(2026, 9, 27))

    # THEN: the request is scoped to the rink's company, date range and ice sheets, in large pages
    params = requests[0].url.params
    assert requests[0].url.path == "/dash/jsonapi/api/v1/events"
    assert params["company"] == "testco"
    assert params["filter[start_date__gte]"] == "2026-09-26"
    assert params["filter[start_date__lte]"] == "2026-09-27"
    assert params["filter[resource_id__in]"] == "1"
    assert params["page[size]"] == "1000"


@patch("searinks.daysmart.client.parse_events")
def test_get_events_follows_pagination_and_sorts_by_start(parse_events: MagicMock) -> None:
    # GIVEN: two pages, with the later event on the first page
    parse_events.side_effect = lambda body, rink: [_event("Late", 18)] if body["page"] == "1" else [_event("Early", 6)]
    requests: list[httpx.Request] = []
    client = _client(last_page=2, requests=requests)

    # WHEN: fetching events
    events = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: both pages are requested and parsed for this rink, and results are sorted by start time
    assert [r.url.params["page[number]"] for r in requests] == ["1", "2"]
    assert all(call.args[1] is RINK for call in parse_events.call_args_list)
    assert [e.title for e in events] == ["Early", "Late"]


@patch("searinks.daysmart.client.parse_events")
def test_get_events_fetches_company_once_for_rinks_sharing_it(parse_events: MagicMock) -> None:
    # GIVEN: two rinks on the same company, each with its own sheet
    parse_events.side_effect = lambda body, rink: [_event(f"{rink.key} event", 9 if rink is SIBLING else 12, rink.key)]
    requests: list[httpx.Request] = []
    client = _client(last_page=1, requests=requests, rinks=[RINK, SIBLING])

    # WHEN: fetching events
    events = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: the company is requested once for both rinks' sheets, the page is parsed for each rink,
    # and events merge by start time
    assert len(requests) == 1
    assert requests[0].url.params["filter[resource_id__in]"] == "1,2"
    assert [call.args[1] for call in parse_events.call_args_list] == [RINK, SIBLING]
    assert [e.title for e in events] == ["sibling event", "test event"]
