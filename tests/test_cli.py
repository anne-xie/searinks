from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.cli import main
from searinks.models.event import Event
from searinks.rinks.kraken import KRAKEN
from searinks.rinks.renton import RENTON

PACIFIC = ZoneInfo("America/Los_Angeles")

EVENTS = [
    Event(
        id="1",
        title="Stick & Puck",
        event_type="Camp",
        rink="kraken",
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
        rink="renton",
        sheet="Renton Large",
        start=datetime(2026, 9, 27, 12, 45, tzinfo=PACIFIC),
        end=datetime(2026, 9, 27, 14, 15, tzinfo=PACIFIC),
    ),
]


@pytest.fixture(autouse=True)
def configure_logging() -> MagicMock:
    """Patch logging setup so CLI runs don't change log levels for other tests."""
    with patch("searinks.cli.configure_logging") as mock:
        yield mock


@pytest.fixture
def get_schedule() -> MagicMock:
    """Patch `get_schedule` as used by the CLI, returning `EVENTS` for the requested rinks."""

    def fake(rinks: list, *args: object, **kwargs: object) -> list[Event]:
        keys = {rink.key for rink in rinks}
        return [e for e in EVENTS if e.rink in keys]

    with patch("searinks.cli.get_schedule", side_effect=fake) as mock:
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
    get_schedule.assert_called_once_with([KRAKEN], date(2026, 9, 26), date(2026, 9, 28), **expected_kwargs)


def test_main_passes_every_requested_rink(get_schedule: MagicMock) -> None:
    # WHEN: asking for two rinks
    main(["kraken", "renton", "--date", "2026-09-26"])

    # THEN: both rinks are fetched together
    assert get_schedule.call_args.args[0] == [KRAKEN, RENTON]


def test_main_prints_single_rink_without_rink_column(
    get_schedule: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    # WHEN: listing one rink's schedule
    main(["kraken", "--date", "2026-09-26", "--days", "2"])

    # THEN: events print under their day with time, sheet, title and open slots
    out = capsys.readouterr().out
    assert out == "Kraken Community Iceplex\n\nSat Sep 26\n  11:15-12:15  Starbucks Rink 1    Stick & Puck  (15/34 open)\n"


def test_main_prints_rink_column_for_multiple_rinks(
    get_schedule: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    # WHEN: listing two rinks
    main(["kraken", "renton", "--date", "2026-09-26", "--days", "2"])

    # THEN: the header names both rinks, events group by day and each row says which rink it's at
    out = capsys.readouterr().out
    assert out == (
        "Kraken Community Iceplex, Sno-King Renton\n"
        "\nSat Sep 26\n"
        "  11:15-12:15  Kraken Community Iceplex  Starbucks Rink 1    Stick & Puck  (15/34 open)\n"
        "\nSun Sep 27\n"
        "  12:45-14:15  Sno-King Renton           Renton Large        Public Skate\n"
    )


@patch("searinks.cli.get_all_schedules", return_value=EVENTS)
def test_main_without_rinks_fetches_all_rinks(
    get_all_schedules: MagicMock, get_schedule: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    # WHEN: no rinks are given
    main(["--date", "2026-09-26", "--days", "2", "--drop-in"])

    # THEN: every rink is fetched with the range and filters, and the header lists every rink
    get_all_schedules.assert_called_once_with(
        date(2026, 9, 26), date(2026, 9, 27), search=None, drop_in=True, sport=None
    )
    get_schedule.assert_not_called()
    out = capsys.readouterr().out
    assert out.startswith(
        "Kraken Community Iceplex, Sno-King Kirkland, Sno-King Renton, Sno-King Snoqualmie, "
        "Olympic View Arena, Lynnwood Ice Center\n"
    )
    assert "  11:15-12:15  Kraken Community Iceplex  Starbucks Rink 1" in out


@pytest.mark.parametrize(("args", "verbose"), [([], False), (["--verbose"], True), (["-v"], True)])
def test_main_configures_logging(
    get_schedule: MagicMock, configure_logging: MagicMock, args: list[str], verbose: bool
) -> None:
    # WHEN: running with or without the verbose flag
    main(["kraken", *args])

    # THEN: logging is set up at the matching verbosity
    configure_logging.assert_called_once_with(verbose=verbose)


@pytest.mark.parametrize("args", [["nope"], ["kraken", "nope"], ["kraken", "--sport", "curling"]])
def test_main_rejects_invalid_arguments(get_schedule: MagicMock, args: list[str]) -> None:
    # WHEN/THEN: an unknown rink or sport exits with an argparse error
    with pytest.raises(SystemExit):
        main(args)
