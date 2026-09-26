import pytest

from searinks.daysmart.source import DaySmartSource
from searinks.models.rink import Rink
from searinks.rectimes.source import RecTimesSource


@pytest.mark.parametrize(
    "source",
    [
        DaySmartSource(company="co", sheets={2: "Rink A", 1: "Rink B"}, drop_in_program_types=frozenset()),
        RecTimesSource(facility="fac", venues={2: "Rink A", 1: "Rink B"}, drop_in_groups=frozenset()),
    ],
)
def test_sheets_lists_sheet_names_in_configured_order(source: DaySmartSource | RecTimesSource) -> None:
    # GIVEN: a rink whose source names two sheets
    rink = Rink(
        key="test",
        name="Test Rink",
        short_name="Test",
        code="TST",
        area="Seattle",
        lat=47.6,
        lng=-122.3,
        timezone="America/Los_Angeles",
        source=source,
    )

    # WHEN/THEN: sheet names come back in the order the source lists them
    assert rink.sheets == ["Rink A", "Rink B"]
