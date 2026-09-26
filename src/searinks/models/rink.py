from dataclasses import dataclass

from searinks.daysmart.source import DaySmartSource
from searinks.rectimes.source import RecTimesSource


@dataclass(frozen=True)
class Rink:
    """A rink and where its schedule is published.

    Args:
        key: Short id used on the command line.
        name: Display name.
        timezone: IANA timezone the rink's local timestamps are in.
        source: Schedule source and its source-specific settings.
    """

    key: str
    name: str
    timezone: str
    source: DaySmartSource | RecTimesSource
