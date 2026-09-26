from dataclasses import dataclass
from datetime import datetime

from searinks.disciplines import discipline_for


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
        return discipline_for(self.sport, self.title)
