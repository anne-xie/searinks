from searinks.rinks import RINKS


def test_kraken_rink_is_registered() -> None:
    # GIVEN/WHEN: looking up the Kraken Community Iceplex
    rink = RINKS["kraken"]

    # THEN: it points at the kraken DaySmart tenant and its three NHL sheets
    assert rink.company == "kraken"
    assert set(rink.sheets) == {1, 2, 3}


def test_snoking_rink_is_registered() -> None:
    # GIVEN/WHEN: looking up Sno-King
    rink = RINKS["snoking"]

    # THEN: it covers all five sheets across Kirkland, Renton and Snoqualmie
    assert rink.company == "snoking"
    assert set(rink.sheets) == {1, 11, 12, 13, 14}
    assert rink.drop_in_program_types == {"Drop-In"}
