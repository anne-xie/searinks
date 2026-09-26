from unittest.mock import MagicMock, patch

from searinks.rectimes.source import RecTimesSource


def test_source_defaults_to_no_overrides() -> None:
    # WHEN: building a source without overrides
    source = RecTimesSource(facility="testfac", venues={1: "Main Rink"}, drop_in_groups=frozenset())

    # THEN: it has an empty override map
    assert source.discipline_overrides == {}


@patch("searinks.rectimes.source.check_overrides")
def test_source_checks_overrides_on_creation(check_overrides: MagicMock) -> None:
    # WHEN: building a source with overrides
    RecTimesSource(facility="testfac", venues={1: "Main Rink"}, drop_in_groups=frozenset(), discipline_overrides={"SJHA": "hockey"})

    # THEN: the overrides are validated
    check_overrides.assert_called_once_with({"SJHA": "hockey"})
