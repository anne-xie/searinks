from searinks.daysmart.source import DaySmartSource
from searinks.models.rink import Rink

KRAKEN = Rink(
    key="kraken",
    name="Kraken Community Iceplex",
    timezone="America/Los_Angeles",
    source=DaySmartSource(
        company="kraken",
        sheets={1: "Starbucks Rink 1", 2: "Smartsheet Rink 2", 3: "VMFH Rink 3"},
        drop_in_program_types=frozenset({"Camp"}),
    ),
)
