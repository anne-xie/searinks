from datetime import date

from searinks.daysmart.client import DaySmartClient
from searinks.models.event import Event
from searinks.models.rink import Rink


def get_schedule(
    rink: Rink,
    start: date,
    end: date,
    *,
    search: str | None = None,
    drop_in: bool = False,
    sport: str | None = None,
) -> list[Event]:
    """Return a rink's events sorted by start time, narrowed by optional filters.

    Args:
        rink: Rink to query.
        start: First day to include.
        end: Last day to include (inclusive).
        search: Case-insensitive substring the title must contain.
        drop_in: Only keep sessions sold per visit.
        sport: Only keep events in this discipline ("hockey", "figure", "public").
    """
    events = DaySmartClient(rink).get_events(start, end)
    if search:
        events = [e for e in events if search.lower() in e.title.lower()]
    if drop_in:
        events = [e for e in events if e.drop_in]
    if sport:
        events = [e for e in events if e.discipline == sport]
    return events
