from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

import httpx

from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rectimes.parse import parse_bookings

BASE_URL = "https://api.rectimes.com/api/v1/facilities"


class RecTimesClient:
    """Reads public calendars from the RecTimes API, one request per facility.

    Args:
        rinks: Rinks to query; their sources must be `RecTimesSource`s on the same facility.
        http: HTTP client; injectable for tests.
    """

    def __init__(self, rinks: Sequence[Rink], http: httpx.Client | None = None) -> None:
        self.rinks = rinks
        self.http = http or httpx.Client(timeout=30)

    def get_events(self, start: date, end: date) -> list[Event]:
        """Return public bookings on every rink's venues sorted by start time.

        Args:
            start: First day to include.
            end: Last day to include (inclusive).
        """
        bookings = self._get_bookings(start, end)
        events = [event for rink in self.rinks for event in parse_bookings(self._own(bookings, rink), rink)]
        return sorted(events, key=lambda e: (e.start, e.rink, e.sheet))

    def _own(self, bookings: list[dict[str, Any]], rink: Rink) -> list[dict[str, Any]]:
        """Drop bookings on the other rinks' venues, so the parser only flags venues no rink knows.

        Args:
            bookings: Raw bookings for every rink on the facility.
            rink: Rink to keep bookings for.
        """
        others = {venue for other in self.rinks if other is not rink for venue in other.source.venues}
        return [b for b in bookings if b.get("venueId") not in others]

    def _get_bookings(self, start: date, end: date) -> list[dict[str, Any]]:
        """Fetch raw bookings from the start of `start` to the end of `end`.

        The API takes rink-local times with a literal "Z" suffix, which is
        what the RecTimes web app sends.

        Args:
            start: First day to include.
            end: Last day to include (inclusive).
        """
        response = self.http.post(
            f"{BASE_URL}/{self.rinks[0].source.facility}/bookings/get_for_calendar",
            json={
                "venueIds": [venue for rink in self.rinks for venue in rink.source.venues],
                "startTimeLocal": f"{start.isoformat()}T00:00:00Z",
                "endTimeLocal": f"{(end + timedelta(days=1)).isoformat()}T00:00:00Z",
            },
        )
        response.raise_for_status()
        return response.json()
