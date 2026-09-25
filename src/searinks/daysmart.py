from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from searinks.rinks import Rink

BASE_URL = "https://apps.daysmartrecreation.com/dash/jsonapi/api/v1"
PAGE_SIZE = 200

DROP_IN_PROGRAM_TYPE = "Camp"
NOT_DROP_IN_SPORTS = {"Private Lessons"}
DISCIPLINE_KEYWORDS = {
    "hockey": ("hockey",),
    "figure": ("freestyle", "fs ", "figure", "dance"),
    "public": ("public skate",),
}


def discipline_for(sport: str | None) -> str | None:
    """Group a DaySmart sport name into "hockey", "figure" or "public".

    Args:
        sport: Sport name as configured by the rink, e.g. "Open Freestyle".

    Returns:
        The discipline, or None when the sport doesn't clearly belong to one.
    """
    name = f"{sport or ''} ".lower()
    for discipline, keywords in DISCIPLINE_KEYWORDS.items():
        if any(k in name for k in keywords):
            return discipline
    return None


@dataclass(frozen=True)
class Event:
    """One scheduled block of ice time.

    Args:
        id: DaySmart event id.
        title: Human-readable name, e.g. "Stick & Puck".
        event_type: DaySmart event type name, e.g. "Camp" or "Rental".
        sheet: Ice sheet name.
        start: Timezone-aware start.
        end: Timezone-aware end.
        open_slots: Remaining registration slots, if DaySmart reports them.
        capacity: Total registration capacity, if DaySmart reports it.
        sport: Sport of the program the event belongs to, e.g. "Hockey".
        drop_in: Whether the event is sold per session rather than as a series.
    """

    id: str
    title: str
    event_type: str
    sheet: str
    start: datetime
    end: datetime
    open_slots: int | None = None
    capacity: int | None = None
    sport: str | None = None
    drop_in: bool = False

    @property
    def discipline(self) -> str | None:
        """Coarse grouping of `sport`; see `discipline_for`."""
        return discipline_for(self.sport)


class DaySmartClient:
    """Reads a rink's public schedule from the DaySmart Recreation JSON:API.

    Args:
        rink: Rink to query.
        http: HTTP client; injectable for tests.
    """

    def __init__(self, rink: Rink, http: httpx.Client | None = None) -> None:
        self.rink = rink
        self.http = http or httpx.Client(timeout=30)
        self.tz = ZoneInfo(rink.timezone)

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
            events.extend(self._parse(body))
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
                "company": self.rink.company,
                "filter[start_date__gte]": start.isoformat(),
                "filter[start_date__lte]": end.isoformat(),
                "include": "eventType,summary,homeTeam.sport,homeTeam.programType",
                "page[size]": PAGE_SIZE,
                "page[number]": page,
            },
        )
        response.raise_for_status()
        return response.json()

    def _parse(self, body: dict[str, Any]) -> list[Event]:
        """Convert a JSON:API page into events, dropping unpublished and off-ice ones.

        Args:
            body: Decoded response body.
        """
        included = {(i["type"], i["id"]): i for i in body.get("included", [])}
        events = []
        for raw in body["data"]:
            attrs = raw["attributes"]
            sheet = self.rink.sheets.get(attrs["resource_id"])
            if sheet is None or not attrs.get("publish"):
                continue
            summary = included.get(("event-summaries", raw["id"]), {}).get("attributes", {})
            event_type = included.get(("event-types", attrs["event_type_id"]), {}).get("attributes", {})
            sport, program_type = self._program(included, attrs.get("hteam_id"))
            events.append(
                Event(
                    id=raw["id"],
                    title=(summary.get("name") or "").strip() or (attrs.get("desc") or "").strip(),
                    event_type=event_type.get("name", attrs["event_type_id"]),
                    sheet=sheet,
                    start=datetime.fromisoformat(attrs["start"]).replace(tzinfo=self.tz),
                    end=datetime.fromisoformat(attrs["end"]).replace(tzinfo=self.tz),
                    open_slots=summary.get("open_slots"),
                    capacity=summary.get("composite_capacity"),
                    sport=sport,
                    drop_in=program_type == DROP_IN_PROGRAM_TYPE and sport not in NOT_DROP_IN_SPORTS,
                )
            )
        return events

    @staticmethod
    def _program(
        included: dict[tuple[str, str], dict[str, Any]], team_id: int | None
    ) -> tuple[str | None, str | None]:
        """Look up the sport and program type names of an event's program.

        DaySmart models programs (stick & puck, a freestyle series, a youth
        team) as "teams"; events without one, like rentals, return (None, None).

        Args:
            included: Sideloaded resources keyed by (type, id).
            team_id: The event's `hteam_id`.
        """
        team = included.get(("teams", str(team_id))) if team_id else None
        if team is None:
            return None, None

        def name(relationship: str) -> str | None:
            ref = team.get("relationships", {}).get(relationship, {}).get("data")
            if ref is None:
                return None
            return included.get((ref["type"], ref["id"]), {}).get("attributes", {}).get("name")

        return name("sport"), name("programType")
