import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from searinks.export import main, to_payload
from searinks.models.event import Event
from searinks.rinks.kraken import KRAKEN

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


@pytest.fixture(autouse=True)
def configure_logging() -> MagicMock:
    """Patch logging setup so export runs don't change log levels for other tests."""
    with patch("searinks.export.configure_logging") as mock:
        yield mock


@pytest.fixture
def get_all_schedules() -> MagicMock:
    """Patch `get_all_schedules` as used by the export, returning `EVENT`."""
    with patch("searinks.export.get_all_schedules", return_value=[EVENT]) as mock:
        yield mock


def test_to_payload_serializes_events_and_rinks() -> None:
    # GIVEN: a generation timestamp
    generated_at = datetime(2026, 9, 26, 8, 0, tzinfo=PACIFIC)

    # WHEN: building the payload for one event at one rink
    payload = to_payload([EVENT], [KRAKEN], generated_at)

    # THEN: timestamps are ISO strings, every event field is kept and rinks carry display metadata
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


def test_to_payload_output_is_json_serializable() -> None:
    # WHEN: dumping the payload
    dumped = json.dumps(to_payload([EVENT], [KRAKEN], datetime(2026, 9, 26, tzinfo=PACIFIC)))

    # THEN: it round-trips to the same events
    assert json.loads(dumped)["events"][0]["title"] == "Stick & Puck"


def test_main_fetches_inclusive_range_unfiltered(get_all_schedules: MagicMock, tmp_path: Path) -> None:
    # WHEN: exporting 14 days from a date
    main(["--date", "2026-09-26", "--days", "14", "--out", str(tmp_path / "events.json")])

    # THEN: every rink is fetched for the inclusive range with no filters
    get_all_schedules.assert_called_once_with(date(2026, 9, 26), date(2026, 10, 9))


def test_main_writes_payload_creating_parent_dirs(get_all_schedules: MagicMock, tmp_path: Path) -> None:
    # GIVEN: an output path whose directory doesn't exist yet
    out = tmp_path / "site" / "events.json"

    # WHEN: exporting
    main(["--date", "2026-09-26", "--out", str(out)])

    # THEN: the file holds the fetched events
    assert [e["id"] for e in json.loads(out.read_text())["events"]] == ["1"]
