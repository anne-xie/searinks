from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from searinks.models.event import Event
from searinks.models.rink import Rink

NOT_DROP_IN_SPORTS = {"Private Lessons"}

Included = dict[tuple[str, str], dict[str, Any]]


def parse_events(body: dict[str, Any], rink: Rink) -> list[Event]:
    """Convert a JSON:API events page into events, dropping unpublished and off-ice ones.

    Args:
        body: Decoded response body.
        rink: Rink the page belongs to; its source must be a `DaySmartSource`.
    """
    tz = ZoneInfo(rink.timezone)
    source = rink.source
    included: Included = {(i["type"], i["id"]): i for i in body.get("included", [])}
    events = []
    for raw in body["data"]:
        attrs = raw["attributes"]
        sheet = source.sheets.get(attrs["resource_id"])
        if sheet is None or not attrs.get("publish"):
            continue
        summary = included.get(("event-summaries", raw["id"]), {}).get("attributes", {})
        event_type = included.get(("event-types", attrs["event_type_id"]), {}).get("attributes", {})
        sport, program_type = _program(included, attrs.get("hteam_id"))
        events.append(
            Event(
                id=raw["id"],
                title=(summary.get("name") or "").strip() or (attrs.get("desc") or "").strip(),
                event_type=event_type.get("name", attrs["event_type_id"]),
                rink=rink.key,
                sheet=sheet,
                start=datetime.fromisoformat(attrs["start"]).replace(tzinfo=tz),
                end=datetime.fromisoformat(attrs["end"]).replace(tzinfo=tz),
                open_slots=summary.get("open_slots"),
                capacity=summary.get("composite_capacity"),
                sport=sport,
                drop_in=program_type in source.drop_in_program_types and sport not in NOT_DROP_IN_SPORTS,
            )
        )
    return events


def _program(included: Included, team_id: int | None) -> tuple[str | None, str | None]:
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
