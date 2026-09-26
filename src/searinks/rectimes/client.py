from datetime import date, timedelta
from typing import Any

import httpx

from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rectimes.parse import parse_bookings

BASE_URL = "https://api.rectimes.com/api/v1/facilities"


class RecTimesClient:
    """Reads a rink's public calendar from the RecTimes API.

    Args:
        rink: Rink to query; its source must be a `RecTimesSource`.
        http: HTTP client; injectable for tests.
    """

    def __init__(self, rink: Rink, http: httpx.Client | None = None) -> None:
        self.rink = rink
        self.http = http or httpx.Client(timeout=30)

    def get_events(self, start: date, end: date) -> list[Event]:
        """Return public bookings on the rink's venues sorted by start time.

        Args:
            start: First day to include.
            end: Last day to include (inclusive).
        """
        events = parse_bookings(self._get_bookings(start, end), self.rink)
        return sorted(events, key=lambda e: (e.start, e.sheet))

    def _get_bookings(self, start: date, end: date) -> list[dict[str, Any]]:
        """Fetch raw bookings from the start of `start` to the end of `end`.

        The API takes rink-local times with a literal "Z" suffix, which is
        what the RecTimes web app sends.

        Args:
            start: First day to include.
            end: Last day to include (inclusive).
        """
        response = self.http.post(
            f"{BASE_URL}/{self.rink.source.facility}/bookings/get_for_calendar",
            json={
                "venueIds": list(self.rink.source.venues),
                "startTimeLocal": f"{start.isoformat()}T00:00:00Z",
                "endTimeLocal": f"{(end + timedelta(days=1)).isoformat()}T00:00:00Z",
            },
        )
        response.raise_for_status()
        return response.json()
