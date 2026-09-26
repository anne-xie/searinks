import pytest

from searinks.disciplines import discipline_for


@pytest.mark.parametrize(
    ("sport", "title", "expected"),
    [
        ("Hockey", "Stick N Puck", "hockey"),
        ("Open Freestyle", "Open Freestyle | Drop-in", "figure"),
        ("FS Club Freestyle", "Aspire Freestyle", "figure"),
        ("FS Group Classes", "On-Ice Class: Edge", "figure"),
        ("Figure Skating", "Freestyle", "figure"),
        ("Ice Dance", "Ice Dance & Testing", "figure"),
        ("Public Skate", "Public Skate Saturdays", "public"),
        ("Ice Skating", "Public Skate", "public"),
        ("Ice Skating", "LTS Practice", None),
        ("Learn to Skate", "FIT Skate", None),
        (None, "Seattle Slapshots vs Seal Team Sticks", None),
        (None, "Kraken Hockey League", "hockey"),
        (None, "Stick & Puck", "hockey"),
        (None, "SJHA STICK & PUCK", "hockey"),
        (None, "OVA Freestyle", "figure"),
        (None, "Theater on Ice", None),
        (None, "Public Skate", "public"),
    ],
)
def test_discipline_for_groups_sport_names(sport: str | None, title: str, expected: str | None) -> None:
    # WHEN/THEN: sport names (or the title, when there is no sport) map to a coarse discipline
    assert discipline_for(sport, title) == expected


@pytest.mark.parametrize(
    ("sport", "title", "expected"),
    [
        (None, "SJHA", "hockey"),
        (None, "Theater on Ice", "figure"),
        ("Hockey", "SJHA", "hockey"),
        (None, "OVA Freestyle", "hockey"),
        (None, "SJHA Tryouts", None),
        (None, "sjha", None),
        (None, "Stick & Puck", "hockey"),
    ],
)
def test_discipline_for_prefers_exact_title_overrides(sport: str | None, title: str, expected: str | None) -> None:
    # GIVEN: a rink that overrides a few exact titles, including one the keywords would call figure
    overrides = {"SJHA": "hockey", "Theater on Ice": "figure", "OVA Freestyle": "hockey"}

    # WHEN/THEN: an exact title match wins; anything else falls back to the shared keywords
    assert discipline_for(sport, title, overrides) == expected
