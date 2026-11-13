from searinks.daysmart.source import DaySmartSource
from searinks.models.rink import Rink

KRAKEN = Rink(
    key="kraken",
    name="Kraken Community Iceplex",
    short_name="KCI",
    code="KCI",
    area="Northgate",
    lat=47.7063,
    lng=-122.3252,
    timezone="America/Los_Angeles",
    source=DaySmartSource(
        company="kraken",
        sheets={1: "Starbucks Rink 1", 2: "Smartsheet Rink 2", 3: "VMFH Rink 3"},
        drop_in_program_types=frozenset({"Camp"}),
    ),
)
