import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from searinks.disciplines import discipline_for
from searinks.models.event import Event
from searinks.models.rink import Rink

logger = logging.getLogger(__name__)

NOT_DROP_IN_SPORTS = {"Private Lessons"}

Included = dict[tuple[str, str], dict[str, Any]]


def parse_events(body: dict[str, Any], rink: Rink) -> list[Event]:
    """Convert a JSON:API events page into events, dropping unpublished and off-ice ones.

    Malformed events are logged and skipped.

    Args:
        body: Decoded response body.
        rink: Rink the page belongs to; its source must be a `DaySmartSource`.
    """
    tz = ZoneInfo(rink.timezone)
    included: Included = {(i["type"], i["id"]): i for i in body.get("included", [])}
    events = []
    for raw in body["data"]:
        try:
            event = _parse_event(raw, included, rink, tz)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(
                "daysmart_event_malformed", extra={"rink": rink.key, "event_id": raw.get("id"), "error": repr(e)}
            )
            continue
        if event is not None:
            events.append(event)
    return events


def _parse_event(raw: dict[str, Any], included: Included, rink: Rink, tz: ZoneInfo) -> Event | None:
    """Convert one event, or return None when it's unpublished or off the rink's ice sheets.

    Args:
        raw: One event resource from the page.
        included: Sideloaded resources keyed by (type, id).
        rink: Rink the event belongs to.
        tz: The rink's timezone.
    """
    source = rink.source
    attrs = raw["attributes"]
    sheet = source.sheets.get(attrs["resource_id"])
    if sheet is None or not attrs.get("publish"):
        return None
    log_extra = {"rink": rink.key, "event_id": raw["id"]}
    summary = included.get(("event-summaries", raw["id"]), {}).get("attributes", {})
    event_type = included.get(("event-types", attrs["event_type_id"]))
    if event_type is None:
        logger.warning("daysmart_event_type_missing", extra={**log_extra, "event_type_id": attrs["event_type_id"]})
    sport, program_type = _program(included, attrs.get("hteam_id"), log_extra)
    title = (summary.get("name") or "").strip() or (attrs.get("desc") or "").strip()
    if not title:
        logger.warning("daysmart_event_untitled", extra=log_extra)
    return Event(
        id=raw["id"],
        title=title,
        event_type=(event_type or {}).get("attributes", {}).get("name", attrs["event_type_id"]),
        rink=rink.key,
        sheet=sheet,
        start=datetime.fromisoformat(attrs["start"]).replace(tzinfo=tz),
        end=datetime.fromisoformat(attrs["end"]).replace(tzinfo=tz),
        open_slots=summary.get("open_slots"),
        capacity=summary.get("composite_capacity"),
        sport=sport,
        drop_in=program_type in source.drop_in_program_types and sport not in NOT_DROP_IN_SPORTS,
        discipline=discipline_for(sport, title, source.discipline_overrides),
    )


def _program(
    included: Included, team_id: int | None, log_extra: dict[str, Any]
) -> tuple[str | None, str | None]:
    """Look up the sport and program type names of an event's program.

    DaySmart models programs (stick & puck, a freestyle series, a youth
    team) as "teams"; events without one, like rentals, return (None, None).
    Programs or program details missing from the sideloaded resources are
    logged and read as None.

    Args:
        included: Sideloaded resources keyed by (type, id).
        team_id: The event's `hteam_id`.
        log_extra: Rink and event fields to attach to warnings.
    """
    if not team_id:
        return None, None
    team = included.get(("teams", str(team_id)))
    if team is None:
        logger.warning("daysmart_program_missing", extra={**log_extra, "team_id": team_id})
        return None, None

    def name(relationship: str) -> str | None:
        ref = team.get("relationships", {}).get(relationship, {}).get("data")
        if ref is None:
            return None
        resource = included.get((ref["type"], ref["id"]))
        if resource is None:
            logger.warning(
                "daysmart_program_incomplete",
                extra={**log_extra, "team_id": team_id, "missing": f"{ref['type']}/{ref['id']}"},
            )
            return None
        return resource.get("attributes", {}).get("name")

    return name("sport"), name("programType")
