from dataclasses import dataclass


@dataclass(frozen=True)
class Rink:
    """A rink whose schedule is published through DaySmart Recreation.

    Args:
        key: Short id used on the command line.
        name: Display name.
        company: DaySmart tenant slug (the `company` query param).
        timezone: IANA timezone the rink's local timestamps are in.
        sheets: DaySmart resource id to ice sheet name. Events on other
            resources (locker rooms, party rooms) are ignored.
        drop_in_program_types: Program type names this rink uses for sessions
            sold per visit; each tenant names these differently.
    """

    key: str
    name: str
    company: str
    timezone: str
    sheets: dict[int, str]
    drop_in_program_types: frozenset[str]
