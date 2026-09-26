from searinks.models.rink import Rink

SNOKING = Rink(
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
)
