from dataclasses import dataclass

from searinks.daysmart.source import DaySmartSource
from searinks.rectimes.source import RecTimesSource


@dataclass(frozen=True)
class Rink:
    """A rink building and where its schedule is published.

    Args:
        key: Short id used on the command line.
        name: Display name.
        short_name: Compact label for tabs and pills, e.g. "KCI".
        code: Three-letter map pin label, e.g. "KCI".
        area: Neighborhood or city the rink is in.
        lat: Latitude of the building.
        lng: Longitude of the building.
        timezone: IANA timezone the rink's local timestamps are in.
        source: Schedule source and its source-specific settings.
    """

    key: str
    name: str
    short_name: str
    code: str
    area: str
    lat: float
    lng: float
    timezone: str
    source: DaySmartSource | RecTimesSource

    @property
    def sheets(self) -> list[str]:
        """Ice sheet names in the order the source lists them."""
        match self.source:
            case DaySmartSource():
                return list(self.source.sheets.values())
            case RecTimesSource():
                return list(self.source.venues.values())
