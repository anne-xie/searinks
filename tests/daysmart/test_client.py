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
    timezone="America/Los_Angeles",
    source=DaySmartSource(company="testco", sheets={1: "Sheet 1"}, drop_in_program_types=frozenset({"Camp"})),
)


def _client(last_page: int, requests: list[httpx.Request]) -> DaySmartClient:
    """Build a client whose HTTP layer returns bodies tagged with their page number.

    Args:
        last_page: `last-page` reported in every response.
        requests: List that captured requests are appended to.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body: dict[str, Any] = {"page": request.url.params["page[number]"], "meta": {"page": {"last-page": last_page}}}
        return httpx.Response(200, json=body)

    return DaySmartClient(RINK, http=httpx.Client(transport=httpx.MockTransport(handler)))


def _event(title: str, hour: int) -> Event:
    """Build an event starting at the given hour.

    Args:
        title: Event title.
        hour: Start hour on 2026-09-26.
    """
    start = datetime(2026, 9, 26, hour)
    return Event(id=title, title=title, event_type="Camp", rink="test", sheet="Sheet 1", start=start, end=start)


@patch("searinks.daysmart.client.parse_events", return_value=[])
def test_get_events_sends_company_and_date_filters(parse_events: MagicMock) -> None:
    # GIVEN: a single page
    requests: list[httpx.Request] = []
    client = _client(last_page=1, requests=requests)

    # WHEN: fetching a date range
    client.get_events(date(2026, 9, 26), date(2026, 9, 27))

    # THEN: the request is scoped to the rink's company and date range
    params = requests[0].url.params
    assert requests[0].url.path == "/dash/jsonapi/api/v1/events"
    assert params["company"] == "testco"
    assert params["filter[start_date__gte]"] == "2026-09-26"
    assert params["filter[start_date__lte]"] == "2026-09-27"


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
