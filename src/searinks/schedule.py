import logging
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Protocol

from searinks.daysmart.client import DaySmartClient
from searinks.daysmart.source import DaySmartSource
from searinks.disciplines import unmatched_overrides
from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rectimes.client import RecTimesClient
from searinks.rectimes.source import RecTimesSource
from searinks.rinks.registry import RINKS

logger = logging.getLogger(__name__)


class ScheduleClient(Protocol):
    """Fetches events for rinks that share one account on a schedule source."""

    def get_events(self, start: date, end: date) -> list[Event]:
        """Return the rinks' events sorted by start time.

        Args:
            start: First day to include.
            end: Last day to include (inclusive).
        """
        ...


def _tenant(rink: Rink) -> tuple[str, str]:
    """Identify the source account a rink's schedule is fetched from.

    Args:
        rink: Rink to identify.
    """
    match rink.source:
        case DaySmartSource():
            return "daysmart", rink.source.company
        case RecTimesSource():
            return "rectimes", rink.source.facility


def tenant_groups(rinks: Sequence[Rink]) -> list[list[Rink]]:
    """Group rinks that share a source account, so each account is fetched once.

    Args:
        rinks: Rinks to group; groups and the rinks in them keep first-seen order.
    """
    groups: dict[tuple[str, str], list[Rink]] = {}
    for rink in rinks:
        groups.setdefault(_tenant(rink), []).append(rink)
    return list(groups.values())


def _client_for(rinks: Sequence[Rink]) -> ScheduleClient:
    """Build the client for a group of rinks sharing one source account.

    Args:
        rinks: Rinks from one `tenant_groups` group.
    """
    match rinks[0].source:
        case DaySmartSource():
            return DaySmartClient(rinks)
        case RecTimesSource():
            return RecTimesClient(rinks)


def _fetch(rinks: Sequence[Rink], start: date, end: date) -> list[Event]:
    """Fetch one source account's events, logging overrides that matched none of their rink's events.

    Args:
        rinks: Rinks from one `tenant_groups` group.
        start: First day to include.
        end: Last day to include (inclusive).
    """
    events = _client_for(rinks).get_events(start, end)
    for rink in rinks:
        titles = (e.title for e in events if e.rink == rink.key)
        for title in unmatched_overrides(rink.source.discipline_overrides, titles):
            logger.debug("discipline_override_unmatched", extra={"rink": rink.key, "title": title})
    return events


def get_schedule(rinks: Sequence[Rink], start: date, end: date) -> list[Event]:
    """Return events across rinks sorted by start time.

    Each source account is fetched once for all of its rinks, accounts are
    fetched in parallel, and results are merged here. A failure fetching any
    account raises.

    Args:
        rinks: Rinks to query.
        start: First day to include.
        end: Last day to include (inclusive).
    """
    groups = tenant_groups(rinks)
    with ThreadPoolExecutor(max_workers=max(len(groups), 1)) as pool:
        per_group = pool.map(lambda group: _fetch(group, start, end), groups)
        events = [event for group_events in per_group for event in group_events]
    return sorted(events, key=lambda e: (e.start, e.rink, e.sheet))


def get_all_schedules(start: date, end: date) -> list[Event]:
    """Return events across every registered rink; see `get_schedule`.

    Args:
        start: First day to include.
        end: Last day to include (inclusive).
    """
    return get_schedule(list(RINKS.values()), start, end)
