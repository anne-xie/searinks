from searinks.daysmart.source import DaySmartSource
from searinks.models.rink import Rink

RENTON = Rink(
    key="renton",
    name="Sno-King Renton",
    short_name="Renton",
    code="REN",
    area="Renton",
    lat=47.4898,
    lng=-122.1212,
    timezone="America/Los_Angeles",
    source=DaySmartSource(
        company="snoking",
        sheets={11: "Renton Large", 12: "Renton Small"},
        drop_in_program_types=frozenset({"Drop-In"}),
    ),
)
