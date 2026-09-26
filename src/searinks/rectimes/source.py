from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecTimesSource:
    """Where a rink publishes its schedule on RecTimes.

    Args:
        facility: RecTimes facility link, e.g. "ova" in `app.rectimes.com/ova`.
            One facility can host several rinks.
        venues: RecTimes venue id to ice sheet name.
        drop_in_groups: Booking group names this rink uses for sessions sold
            per visit; RecTimes has no drop-in flag of its own.
        discipline_overrides: Exact event title to discipline ("hockey",
            "figure", "public") for titles the shared keywords miss or get wrong.
    """

    facility: str
    venues: dict[int, str]
    drop_in_groups: frozenset[str]
    discipline_overrides: dict[str, str] = field(default_factory=dict)
