from dataclasses import dataclass, field

from searinks.disciplines import check_overrides


@dataclass(frozen=True)
class DaySmartSource:
    """Where a rink publishes its schedule on DaySmart Recreation.

    Args:
        company: DaySmart tenant slug (the `company` query param).
        sheets: DaySmart resource id to ice sheet name. Events on other
            resources (locker rooms, party rooms) are ignored.
        drop_in_program_types: Program type names this rink uses for sessions
            sold per visit; each tenant names these differently.
        discipline_overrides: Exact event title to discipline ("hockey",
            "figure", "public") for titles the shared keywords miss or get wrong.
    """

    company: str
    sheets: dict[int, str]
    drop_in_program_types: frozenset[str]
    discipline_overrides: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Reject overrides to unknown disciplines."""
        check_overrides(self.discipline_overrides)
