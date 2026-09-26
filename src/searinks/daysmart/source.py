from dataclasses import dataclass


@dataclass(frozen=True)
class DaySmartSource:
    """Where a rink publishes its schedule on DaySmart Recreation.

    Args:
        company: DaySmart tenant slug (the `company` query param).
        sheets: DaySmart resource id to ice sheet name. Events on other
            resources (locker rooms, party rooms) are ignored.
        drop_in_program_types: Program type names this rink uses for sessions
            sold per visit; each tenant names these differently.
    """

    company: str
    sheets: dict[int, str]
    drop_in_program_types: frozenset[str]
