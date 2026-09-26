from dataclasses import dataclass
from datetime import datetime

from searinks.disciplines import discipline_for


@dataclass(frozen=True)
class Event:
    """One scheduled block of ice time.

    Args:
        id: Event id within its source.
        title: Human-readable name, e.g. "Stick & Puck".
        rink: Key of the rink the event is at.
        sheet: Ice sheet name.
        start: Timezone-aware start.
        end: Timezone-aware end.
        event_type: Source's event type name, e.g. "Camp" or "Rental", if it has one.
        open_slots: Remaining registration slots, if the source reports them.
        capacity: Total registration capacity, if the source reports it.
        sport: Sport of the program the event belongs to, e.g. "Hockey".
        drop_in: Whether the event is sold per session rather than as a series.
    """

    id: str
    title: str
    rink: str
    sheet: str
    start: datetime
    end: datetime
    event_type: str | None = None
    open_slots: int | None = None
    capacity: int | None = None
    sport: str | None = None
    drop_in: bool = False

    @property
    def discipline(self) -> str | None:
        """Coarse grouping of `sport`; see `discipline_for`."""
        return discipline_for(self.sport, self.title)
