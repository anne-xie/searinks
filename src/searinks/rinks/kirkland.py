from searinks.daysmart.source import DaySmartSource
from searinks.models.rink import Rink

KIRKLAND = Rink(
    key="kirkland",
    name="Sno-King Kirkland",
    short_name="Sno-King Kirkland",
    code="KIR",
    area="Kirkland",
    lat=47.7304,
    lng=-122.1737,
    timezone="America/Los_Angeles",
    source=DaySmartSource(
        company="snoking",
        sheets={1: "Kirkland"},
        drop_in_program_types=frozenset({"Drop-In"}),
    ),
)
