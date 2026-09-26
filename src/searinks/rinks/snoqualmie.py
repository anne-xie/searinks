from searinks.daysmart.source import DaySmartSource
from searinks.models.rink import Rink

SNOQUALMIE = Rink(
    key="snoqualmie",
    name="Sno-King Snoqualmie",
    short_name="Snoqualmie",
    code="SNQ",
    area="Snoqualmie",
    lat=47.5248,
    lng=-121.8689,
    timezone="America/Los_Angeles",
    source=DaySmartSource(
        company="snoking",
        sheets={13: "Snoqualmie A", 14: "Snoqualmie B"},
        drop_in_program_types=frozenset({"Drop-In"}),
    ),
)
