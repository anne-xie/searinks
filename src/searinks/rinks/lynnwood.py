from searinks.models.rink import Rink
from searinks.rectimes.source import RecTimesSource

LYNNWOOD = Rink(
    key="lynnwood",
    name="Lynnwood Ice Center",
    short_name="Lynnwood",
    code="LIC",
    area="Lynnwood",
    lat=47.8194,
    lng=-122.3249,
    timezone="America/Los_Angeles",
    source=RecTimesSource(
        facility="ova",
        venues={1146: "Main Rink"},
        drop_in_groups=frozenset({"Stick & Puck", "Public Skate", "LIC Freestyle", "Adult Drop in"}),
        discipline_overrides={
            "SJHA": "hockey",
            "Seattle Selects": "hockey",
            "Arctic Foxes": "hockey",
            "Spicy Kittens": "hockey",
            "Theater on Ice": "figure",
        },
    ),
)
