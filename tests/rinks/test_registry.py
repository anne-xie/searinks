from searinks.rinks.registry import RINKS


def test_registry_includes_every_rink() -> None:
    # WHEN/THEN: every supported rink is available by name, with Sno-King split by building
    assert set(RINKS) == {"kraken", "kirkland", "renton", "snoqualmie", "ova", "lynnwood"}


def test_registry_keys_match_rink_keys() -> None:
    # WHEN/THEN: each rink is registered under its own key
    assert all(key == rink.key for key, rink in RINKS.items())


def test_registry_codes_are_unique() -> None:
    # WHEN/THEN: no two rinks share a map pin code
    codes = [rink.code for rink in RINKS.values()]
    assert len(codes) == len(set(codes))


def test_registry_coordinates_are_in_the_seattle_area() -> None:
    # WHEN/THEN: every rink sits in a box around greater Seattle, so swapped or mistyped lat/lng stand out
    assert all(47.0 < rink.lat < 48.2 and -122.6 < rink.lng < -121.5 for rink in RINKS.values())
