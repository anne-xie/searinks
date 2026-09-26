from searinks.models.rink import Rink

KRAKEN = Rink(
    key="kraken",
    name="Kraken Community Iceplex",
    company="kraken",
    timezone="America/Los_Angeles",
    sheets={1: "Starbucks Rink 1", 2: "Smartsheet Rink 2", 3: "VMFH Rink 3"},
    drop_in_program_types=frozenset({"Camp"}),
)
