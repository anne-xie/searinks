from searinks.models.rink import Rink
from searinks.rectimes.source import RecTimesSource

OVA = Rink(
    key="ova",
    name="Olympic View Arena",
    timezone="America/Los_Angeles",
    source=RecTimesSource(
        facility="ova",
        venues={1145: "Main Rink"},
        drop_in_groups=frozenset({"OVA Freestyle", "OVA Lunch Hockey", "Friday Night Skates"}),
    ),
)
