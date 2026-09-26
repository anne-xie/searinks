import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import httpx

from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rectimes.client import RecTimesClient
from searinks.rectimes.source import RecTimesSource

RINK = Rink(
    key="test",
    name="Test Rink",
    timezone="America/Los_Angeles",
    source=RecTimesSource(facility="testfac", venues={10: "Main Rink", 11: "Studio"}, drop_in_groups=frozenset()),
)


def _client(body: list, requests: list[httpx.Request]) -> RecTimesClient:
    """Build a client whose HTTP layer always returns the given body.

    Args:
        body: Decoded JSON body every response carries.
        requests: List that captured requests are appended to.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=body)

    return RecTimesClient(RINK, http=httpx.Client(transport=httpx.MockTransport(handler)))


def _event(title: str, hour: int) -> Event:
    """Build an event starting at the given hour.

    Args:
        title: Event title.
        hour: Start hour on 2026-09-26.
    """
    start = datetime(2026, 9, 26, hour)
    return Event(id=title, title=title, rink="test", sheet="Main Rink", start=start, end=start)


@patch("searinks.rectimes.client.parse_bookings", return_value=[])
def test_get_events_posts_venues_and_local_day_range(parse_bookings: MagicMock) -> None:
    # GIVEN: a client for a rink with two venues
    requests: list[httpx.Request] = []
    client = _client([], requests)

    # WHEN: fetching a two-day range
    client.get_events(date(2026, 9, 26), date(2026, 9, 27))

    # THEN: one calendar request covers the rink's venues from the first day through the end of the last
    (request,) = requests
    assert request.method == "POST"
    assert request.url == "https://api.rectimes.com/api/v1/facilities/testfac/bookings/get_for_calendar"
    assert json.loads(request.content) == {
        "venueIds": [10, 11],
        "startTimeLocal": "2026-09-26T00:00:00Z",
        "endTimeLocal": "2026-09-28T00:00:00Z",
    }


@patch("searinks.rectimes.client.parse_bookings")
def test_get_events_parses_for_this_rink_and_sorts_by_start(parse_bookings: MagicMock) -> None:
    # GIVEN: the parser returns events out of order
    parse_bookings.return_value = [_event("Late", 18), _event("Early", 6)]
    body = [{"id": 1}]
    client = _client(body, [])

    # WHEN: fetching events
    events = client.get_events(date(2026, 9, 26), date(2026, 9, 26))

    # THEN: the response is parsed for this rink and results are sorted by start time
    parse_bookings.assert_called_once_with(body, RINK)
    assert [e.title for e in events] == ["Early", "Late"]
