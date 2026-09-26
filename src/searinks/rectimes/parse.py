import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from searinks.disciplines import discipline_for
from searinks.models.event import Event
from searinks.models.rink import Rink

logger = logging.getLogger(__name__)


def parse_bookings(body: list[dict[str, Any]], rink: Rink) -> list[Event]:
    """Convert RecTimes calendar bookings into events, dropping hidden ones and other venues.

    RecTimes' `eventTypeName` is a per-venue default rather than a real type,
    so events carry no `event_type` or `sport`. Malformed bookings are logged
    and skipped.

    Args:
        body: Decoded `get_for_calendar` response.
        rink: Rink the bookings belong to.
    """
    tz = ZoneInfo(rink.timezone)
    events = []
    for raw in body:
        try:
            event = _parse_booking(raw, rink, tz)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(
                "rectimes_booking_malformed", extra={"rink": rink.key, "booking_id": raw.get("id"), "error": repr(e)}
            )
            continue
        if event is not None:
            events.append(event)
    return events


def _parse_booking(raw: dict[str, Any], rink: Rink, tz: ZoneInfo) -> Event | None:
    """Convert one booking, or return None when it isn't a public booking on the rink's venues.

    Args:
        raw: One booking from the response.
        rink: Rink the booking belongs to.
        tz: The rink's timezone.
    """
    if raw.get("hiddenFromPublic"):
        return None
    source = rink.source
    log_extra = {"rink": rink.key, "booking_id": raw["id"]}
    sheet = source.venues.get(raw["venueId"])
    if sheet is None:
        logger.warning("rectimes_booking_unknown_venue", extra={**log_extra, "venue_id": raw["venueId"]})
        return None
    group = (raw.get("groupName") or "").strip()
    title = (raw.get("eventName") or "").strip() or group
    if not title:
        logger.warning("rectimes_booking_untitled", extra=log_extra)
    return Event(
        id=str(raw["id"]),
        title=title,
        rink=rink.key,
        sheet=sheet,
        start=datetime.fromisoformat(raw["startTimeLocal"]).replace(tzinfo=tz),
        end=datetime.fromisoformat(raw["endTimeLocal"]).replace(tzinfo=tz),
        drop_in=group in source.drop_in_groups,
        discipline=discipline_for(None, title, source.discipline_overrides),
    )
