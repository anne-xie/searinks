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


RINKS: dict[str, Rink] = {
    rink.key: rink
    for rink in [
        Rink(
            key="kraken",
            name="Kraken Community Iceplex",
            company="kraken",
            timezone="America/Los_Angeles",
            sheets={1: "Starbucks Rink 1", 2: "Smartsheet Rink 2", 3: "VMFH Rink 3"},
            drop_in_program_types=frozenset({"Camp"}),
        ),
        Rink(
            key="snoking",
            name="Sno-King Ice Arenas",
            company="snoking",
            timezone="America/Los_Angeles",
            sheets={
                1: "Kirkland",
                11: "Renton Large",
                12: "Renton Small",
                13: "Snoqualmie A",
                14: "Snoqualmie B",
            },
            drop_in_program_types=frozenset({"Drop-In"}),
        ),
    ]
}
