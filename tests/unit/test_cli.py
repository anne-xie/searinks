from datetime import date, datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.cli import main
from searinks.daysmart import Event

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
        sport="Hockey",
        drop_in=True,
    ),
    Event(
        id="2",
        title="Public Skate Saturdays",
        event_type="Camp",
        sheet="VMFH Rink 3",
        start=datetime(2026, 9, 26, 12, 45, tzinfo=PACIFIC),
        end=datetime(2026, 9, 26, 14, 15, tzinfo=PACIFIC),
        open_slots=296,
        capacity=300,
        sport="Public Skate",
        drop_in=True,
    ),
    Event(
        id="3",
        title="Sat 7:00-8:00am | Open Freestyle | Pre-Paid",
        event_type="Class",
        sheet="Smartsheet Rink 2",
        start=datetime(2026, 9, 26, 7, 0, tzinfo=PACIFIC),
        end=datetime(2026, 9, 26, 8, 0, tzinfo=PACIFIC),
        sport="Open Freestyle",
        drop_in=False,
    ),
    Event(
        id="4",
        title="Seattle Slapshots vs Seal Team Sticks",
        event_type="League Game",
        sheet="Starbucks Rink 1",
        start=datetime(2026, 9, 26, 16, 10, tzinfo=PACIFIC),
        end=datetime(2026, 9, 26, 17, 25, tzinfo=PACIFIC),
        sport="Hockey",
        drop_in=False,
    ),
]


@pytest.fixture
def client() -> MagicMock:
    """Patch the DaySmart client used by the CLI and return the instance mock."""
    with patch("searinks.cli.DaySmartClient") as cls:
        cls.return_value.get_events.return_value = EVENTS
        yield cls.return_value


def test_main_fetches_requested_date_range(client: MagicMock) -> None:
    # WHEN: asking for 3 days starting on a date
    main(["kraken", "--date", "2026-09-26", "--days", "3"])

    # THEN: the client is queried for the inclusive range
    client.get_events.assert_called_once_with(date(2026, 9, 26), date(2026, 9, 28))


def test_main_prints_events(client: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    # WHEN: listing a day's schedule
    main(["kraken", "--date", "2026-09-26"])

    # THEN: each event is printed with its time, sheet and title
    out = capsys.readouterr().out
    assert "Sat Sep 26" in out
    assert "11:15-12:15" in out
    assert "Starbucks Rink 1" in out
    assert "Public Skate Saturdays" in out


def test_main_filters_by_search_term(client: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    # WHEN: searching case-insensitively for public skate
    main(["kraken", "--date", "2026-09-26", "--search", "public skate"])

    # THEN: only matching events are printed
    out = capsys.readouterr().out
    assert "Public Skate Saturdays" in out
    assert "Stick & Puck" not in out


@pytest.mark.parametrize(
    ("args", "expected_ids"),
    [
        (["--drop-in"], {"1", "2"}),
        (["--sport", "hockey"], {"1", "4"}),
        (["--sport", "figure"], {"3"}),
        (["--drop-in", "--sport", "hockey"], {"1"}),
        (["--drop-in", "--search", "stick"], {"1"}),
    ],
)
def test_main_filters_by_drop_in_and_sport(
    client: MagicMock, capsys: pytest.CaptureFixture[str], args: list[str], expected_ids: set[str]
) -> None:
    # WHEN: listing with drop-in / sport filters
    main(["kraken", "--date", "2026-09-26", *args])

    # THEN: only the matching events are printed
    out = capsys.readouterr().out
    printed = {e.id for e in EVENTS if e.title in out}
    assert printed == expected_ids


def test_main_rejects_unknown_rink(client: MagicMock) -> None:
    # WHEN/THEN: an unregistered rink key exits with an argparse error
    with pytest.raises(SystemExit):
        main(["nope"])
