from unittest.mock import MagicMock, patch

from searinks.daysmart.source import DaySmartSource


def test_source_defaults_to_no_overrides() -> None:
    # WHEN: building a source without overrides
    source = DaySmartSource(company="testco", sheets={1: "Sheet 1"}, drop_in_program_types=frozenset())

    # THEN: it has an empty override map
    assert source.discipline_overrides == {}


@patch("searinks.daysmart.source.check_overrides")
def test_source_checks_overrides_on_creation(check_overrides: MagicMock) -> None:
    # WHEN: building a source with overrides
    DaySmartSource(company="testco", sheets={1: "Sheet 1"}, drop_in_program_types=frozenset(), discipline_overrides={"SJHA": "hockey"})

    # THEN: the overrides are validated
    check_overrides.assert_called_once_with({"SJHA": "hockey"})
