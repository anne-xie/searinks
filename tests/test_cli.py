from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.cli import main
from searinks.models.event import Event
from searinks.rinks.kraken import KRAKEN

PACIFIC = ZoneInfo("America/Los_Angeles")

EVENTS = [
    Event(
        id="1",
        title="Stick & Puck",
        event_type="Camp",
        sheet="Starbucks Rink 1",
        start=datetime(2026, 9, 26, 11, 15, tzinfo=PACIFIC),
        end=datetime(2026, 9, 26, 12, 15, tzinfo=PACIFIC),
        open_slots=15,
        capacity=34,
    ),
    Event(
        id="2",
        title="Public Skate",
        event_type="Camp",
        sheet="VMFH Rink 3",
        start=datetime(2026, 9, 27, 12, 45, tzinfo=PACIFIC),
        end=datetime(2026, 9, 27, 14, 15, tzinfo=PACIFIC),
    ),
]


@pytest.fixture
def get_schedule() -> MagicMock:
    """Patch `get_schedule` as used by the CLI."""
    with patch("searinks.cli.get_schedule", return_value=EVENTS) as mock:
        yield mock


@pytest.mark.parametrize(
    ("args", "expected_kwargs"),
    [
        ([], {"search": None, "drop_in": False, "sport": None}),
        (["--search", "stick"], {"search": "stick", "drop_in": False, "sport": None}),
        (["--drop-in", "--sport", "hockey"], {"search": None, "drop_in": True, "sport": "hockey"}),
    ],
)
def test_main_passes_rink_range_and_filters(get_schedule: MagicMock, args: list[str], expected_kwargs: dict) -> None:
    # WHEN: asking for 3 days starting on a date with the given flags
    main(["kraken", "--date", "2026-09-26", "--days", "3", *args])

    # THEN: the schedule is fetched for the rink, the inclusive range and the filters
    get_schedule.assert_called_once_with(KRAKEN, date(2026, 9, 26), date(2026, 9, 28), **expected_kwargs)


def test_main_prints_events_grouped_by_day(get_schedule: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    # WHEN: listing the schedule
    main(["kraken", "--date", "2026-09-26", "--days", "2"])

    # THEN: events print under their day with time, sheet, title and open slots
    out = capsys.readouterr().out
    assert "Kraken Community Iceplex" in out
    assert "Sat Sep 26" in out
    assert "11:15-12:15  Starbucks Rink 1    Stick & Puck  (15/34 open)" in out
    assert "Sun Sep 27" in out
    assert "12:45-14:15  VMFH Rink 3         Public Skate\n" in out


@pytest.mark.parametrize("args", [["nope"], ["kraken", "--sport", "curling"]])
def test_main_rejects_invalid_arguments(get_schedule: MagicMock, args: list[str]) -> None:
    # WHEN/THEN: an unknown rink or sport exits with an argparse error
    with pytest.raises(SystemExit):
        main(args)
