from searinks.rinks.registry import RINKS


def test_registry_includes_every_rink() -> None:
    # WHEN/THEN: every supported rink is available by name
    assert set(RINKS) == {"kraken", "snoking"}


def test_registry_keys_match_rink_keys() -> None:
    # WHEN/THEN: each rink is registered under its own key
    assert all(key == rink.key for key, rink in RINKS.items())
