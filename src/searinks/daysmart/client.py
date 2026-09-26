from datetime import date
from typing import Any

import httpx

from searinks.daysmart.parse import parse_events
from searinks.models.event import Event
from searinks.models.rink import Rink

BASE_URL = "https://apps.daysmartrecreation.com/dash/jsonapi/api/v1"
PAGE_SIZE = 200


class DaySmartClient:
    """Reads a rink's public schedule from the DaySmart Recreation JSON:API.

    Args:
        rink: Rink to query; its source must be a `DaySmartSource`.
        http: HTTP client; injectable for tests.
    """

    def __init__(self, rink: Rink, http: httpx.Client | None = None) -> None:
        self.rink = rink
        self.http = http or httpx.Client(timeout=30)

    def get_events(self, start: date, end: date) -> list[Event]:
        """Return published ice-sheet events sorted by start time.

        Args:
            start: First day to include.
            end: Last day to include (inclusive).
        """
        events: list[Event] = []
        page, last_page = 1, 1
        while page <= last_page:
            body = self._get_page(start, end, page)
            events.extend(parse_events(body, self.rink))
            last_page = body.get("meta", {}).get("page", {}).get("last-page", 1)
            page += 1
        return sorted(events, key=lambda e: (e.start, e.sheet))

    def _get_page(self, start: date, end: date, page: int) -> dict[str, Any]:
        """Fetch one page of raw events.

        Args:
            start: First day to include.
            end: Last day to include (inclusive).
            page: 1-based page number.
        """
        response = self.http.get(
            f"{BASE_URL}/events",
            params={
                "company": self.rink.source.company,
                "filter[start_date__gte]": start.isoformat(),
                "filter[start_date__lte]": end.isoformat(),
                "include": "eventType,summary,homeTeam.sport,homeTeam.programType",
                "page[size]": PAGE_SIZE,
                "page[number]": page,
            },
        )
        response.raise_for_status()
        return response.json()
