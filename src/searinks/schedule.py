from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from searinks.daysmart.client import DaySmartClient
from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rinks.registry import RINKS


def get_schedule(
    rinks: Sequence[Rink],
    start: date,
    end: date,
    *,
    search: str | None = None,
    drop_in: bool = False,
    sport: str | None = None,
) -> list[Event]:
    """Return events across rinks sorted by start time, narrowed by optional filters.

    DaySmart only serves one tenant per request, so rinks are fetched in parallel
    and merged here. A failure fetching any rink raises.

    Args:
        rinks: Rinks to query.
        start: First day to include.
        end: Last day to include (inclusive).
        search: Case-insensitive substring the title must contain.
        drop_in: Only keep sessions sold per visit.
        sport: Only keep events in this discipline ("hockey", "figure", "public").
    """
    with ThreadPoolExecutor(max_workers=max(len(rinks), 1)) as pool:
        per_rink = pool.map(lambda rink: DaySmartClient(rink).get_events(start, end), rinks)
        events = [event for rink_events in per_rink for event in rink_events]
    if search:
        events = [e for e in events if search.lower() in e.title.lower()]
    if drop_in:
        events = [e for e in events if e.drop_in]
    if sport:
        events = [e for e in events if e.discipline == sport]
    return sorted(events, key=lambda e: (e.start, e.rink, e.sheet))


def get_all_schedules(
    start: date,
    end: date,
    *,
    search: str | None = None,
    drop_in: bool = False,
    sport: str | None = None,
) -> list[Event]:
    """Return events across every registered rink; see `get_schedule`.

    Args:
        start: First day to include.
        end: Last day to include (inclusive).
        search: Case-insensitive substring the title must contain.
        drop_in: Only keep sessions sold per visit.
        sport: Only keep events in this discipline ("hockey", "figure", "public").
    """
    return get_schedule(list(RINKS.values()), start, end, search=search, drop_in=drop_in, sport=sport)
