from searinks.models.rink import Rink
from searinks.rectimes.source import RecTimesSource

OVA = Rink(
    key="ova",
    name="Olympic View Arena",
    short_name="Olympic View",
    code="OVA",
    area="Mountlake Terrace",
    lat=47.7971,
    lng=-122.3284,
    timezone="America/Los_Angeles",
    source=RecTimesSource(
        facility="ova",
        venues={1145: "Main Rink"},
        drop_in_groups=frozenset({"OVA Freestyle", "OVA Lunch Hockey", "Friday Night Skates"}),
        discipline_overrides={"SJHA": "hockey", "OVHL": "hockey", "Seattle Selects": "hockey", "SSC": "figure"},
    ),
)
