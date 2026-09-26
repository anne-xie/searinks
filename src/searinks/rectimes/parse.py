from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from searinks.models.event import Event
from searinks.models.rink import Rink


def parse_bookings(body: list[dict[str, Any]], rink: Rink) -> list[Event]:
    """Convert RecTimes calendar bookings into events, dropping hidden ones and other venues.

    RecTimes' `eventTypeName` is a per-venue default rather than a real type,
    so events carry no `event_type` or `sport`.

    Args:
        body: Decoded `get_for_calendar` response.
        rink: Rink the bookings belong to.
    """
    tz = ZoneInfo(rink.timezone)
    source = rink.source
    events = []
    for raw in body:
        sheet = source.venues.get(raw["venueId"])
        if sheet is None or raw.get("hiddenFromPublic"):
            continue
        group = (raw.get("groupName") or "").strip()
        events.append(
            Event(
                id=str(raw["id"]),
                title=(raw.get("eventName") or "").strip() or group,
                rink=rink.key,
                sheet=sheet,
                start=datetime.fromisoformat(raw["startTimeLocal"]).replace(tzinfo=tz),
                end=datetime.fromisoformat(raw["endTimeLocal"]).replace(tzinfo=tz),
                drop_in=group in source.drop_in_groups,
            )
        )
    return events
