import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.export import day_payloads, main, rinks_payload
from searinks.models.event import Event
from searinks.rinks.kraken import KRAKEN
from searinks.rinks.registry import RINKS

PACIFIC = ZoneInfo("America/Los_Angeles")

EVENT = Event(
    id="1",
    title="Stick & Puck",
    rink="kraken",
    sheet="Starbucks Rink 1",
    start=datetime(2026, 9, 26, 11, 15, tzinfo=PACIFIC),
    end=datetime(2026, 9, 26, 12, 15, tzinfo=PACIFIC),
    event_type="Camp",
    open_slots=15,
    capacity=34,
    sport="Hockey",
    drop_in=True,
    discipline="hockey",
)

LATER_EVENT = Event(
    id="2",
    title="Public Skate",
    rink="kraken",
    sheet="Smartsheet Rink 2",
    start=datetime(2026, 9, 28, 23, 30, tzinfo=PACIFIC),
    end=datetime(2026, 9, 29, 0, 30, tzinfo=PACIFIC),
)
GENERATED_AT = datetime(2026, 9, 26, 8, 0, tzinfo=PACIFIC)


@pytest.fixture(autouse=True)
def configure_logging() -> MagicMock:
    """Patch logging setup so export runs don't change log levels for other tests."""
    with patch("searinks.export.configure_logging") as mock:
        yield mock


@pytest.fixture
def get_all_schedules() -> MagicMock:
    """Patch `get_all_schedules` as used by the export, returning `EVENT` and `LATER_EVENT`."""
    with patch("searinks.export.get_all_schedules", return_value=[EVENT, LATER_EVENT]) as mock:
        yield mock


def _event_ids(path: Path) -> list[str]:
    """Read the event ids from an exported day file.

    Args:
        path: Day file to read.
    """
    return [e["id"] for e in json.loads(path.read_text())["events"]]


def test_rinks_payload_serializes_display_metadata() -> None:
    # WHEN: building the rinks payload
    payload = rinks_payload([KRAKEN], GENERATED_AT)

    # THEN: each rink carries its display metadata but not its schedule source
    assert payload == {
        "generated_at": "2026-09-26T08:00:00-07:00",
        "rinks": [
            {
                "key": "kraken",
                "name": "Kraken Community Iceplex",
                "short_name": "Kraken",
                "code": "KCI",
                "area": "Northgate",
                "lat": 47.7063,
                "lng": -122.3252,
                "sheets": ["Starbucks Rink 1", "Smartsheet Rink 2", "VMFH Rink 3"],
            }
        ],
    }


def test_day_payloads_serializes_every_event_field() -> None:
    # WHEN: building the payload for a single day with one event
    payloads = day_payloads([EVENT], date(2026, 9, 26), date(2026, 9, 26), GENERATED_AT)

    # THEN: the day's file has its date, timestamp and every event field with ISO times
    assert payloads == {
        date(2026, 9, 26): {
            "date": "2026-09-26",
            "generated_at": "2026-09-26T08:00:00-07:00",
            "events": [
                {
                    "id": "1",
                    "title": "Stick & Puck",
                    "rink": "kraken",
                    "sheet": "Starbucks Rink 1",
                    "start": "2026-09-26T11:15:00-07:00",
                    "end": "2026-09-26T12:15:00-07:00",
                    "event_type": "Camp",
                    "open_slots": 15,
                    "capacity": 34,
                    "sport": "Hockey",
                    "drop_in": True,
                    "discipline": "hockey",
                }
            ],
        }
    }


def test_day_payloads_groups_by_start_day_and_keeps_empty_days() -> None:
    # GIVEN: events on the first and third day, the later one running past midnight
    events = [EVENT, LATER_EVENT]

    # WHEN: building payloads for a four-day range
    payloads = day_payloads(events, date(2026, 9, 26), date(2026, 9, 29), GENERATED_AT)

    # THEN: every day in the range gets a payload, events land on the day they start
    assert {day: [e["id"] for e in p["events"]] for day, p in payloads.items()} == {
        date(2026, 9, 26): ["1"],
        date(2026, 9, 27): [],
        date(2026, 9, 28): ["2"],
        date(2026, 9, 29): [],
    }


def test_day_payloads_drops_events_outside_range() -> None:
    # WHEN: building payloads for a range that excludes the later event
    payloads = day_payloads([EVENT, LATER_EVENT], date(2026, 9, 26), date(2026, 9, 27), GENERATED_AT)

    # THEN: only in-range days and events are present
    assert {day: [e["id"] for e in p["events"]] for day, p in payloads.items()} == {
        date(2026, 9, 26): ["1"],
        date(2026, 9, 27): [],
    }


def test_main_fetches_inclusive_range_unfiltered(get_all_schedules: MagicMock, tmp_path: Path) -> None:
    # WHEN: exporting 14 days from a date
    main(["--date", "2026-09-26", "--days", "14", "--out-dir", str(tmp_path)])

    # THEN: every rink is fetched for the inclusive range with no filters
    get_all_schedules.assert_called_once_with(date(2026, 9, 26), date(2026, 10, 9))


def test_main_writes_rinks_and_one_file_per_day(get_all_schedules: MagicMock, tmp_path: Path) -> None:
    # GIVEN: an output directory that doesn't exist yet
    out = tmp_path / "site" / "data"

    # WHEN: exporting three days
    main(["--date", "2026-09-26", "--days", "3", "--out-dir", str(out)])

    # THEN: rinks.json lists every rink and each day's file holds that day's events
    assert len(json.loads((out / "rinks.json").read_text())["rinks"]) == len(RINKS)
    assert sorted(p.name for p in (out / "days").iterdir()) == ["2026-09-26.json", "2026-09-27.json", "2026-09-28.json"]
    assert [_event_ids(out / "days" / f"2026-09-{d}.json") for d in (26, 27, 28)] == [["1"], [], ["2"]]


def test_main_leaves_days_outside_range_untouched(get_all_schedules: MagicMock, tmp_path: Path) -> None:
    # GIVEN: a previously exported day outside the range being refreshed
    (tmp_path / "days").mkdir()
    (tmp_path / "days" / "2026-09-25.json").write_text("previous")

    # WHEN: refreshing a single later day
    main(["--date", "2026-09-26", "--days", "1", "--out-dir", str(tmp_path)])

    # THEN: the earlier day's file is left as it was
    assert (tmp_path / "days" / "2026-09-25.json").read_text() == "previous"
