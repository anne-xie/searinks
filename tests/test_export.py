import json
import logging
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import httpx
import pytest

from searinks.export import day_payloads, main, rinks_payload
from searinks.models.event import Event
from searinks.models.rink import Rink
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
def get_schedule() -> MagicMock:
    """Patch `get_schedule` as used by the export: Kraken serves `EVENT` and `LATER_EVENT`, other rinks nothing."""

    def fake(rinks: list[Rink], start: date, end: date) -> list[Event]:
        return [EVENT, LATER_EVENT] if rinks == [KRAKEN] else []

    with patch("searinks.export.get_schedule", side_effect=fake) as mock:
        yield mock


def _event_ids(path: Path) -> list[str]:
    """Read the event ids from an exported rink-day file.

    Args:
        path: Rink-day file to read.
    """
    return [e["id"] for e in json.loads(path.read_text())["events"]]


def _written(out: Path) -> list[str]:
    """List exported rink-day files as `<date>/<rink>.json`.

    Args:
        out: Export output directory.
    """
    return sorted(str(p.relative_to(out / "days")) for p in (out / "days").glob("*/*.json"))


def _fail(get_schedule: MagicMock, errors: dict[str, Exception]) -> None:
    """Make the patched `get_schedule` raise for groups holding some rinks and serve the rest as before.

    Args:
        get_schedule: The patched `get_schedule` fixture.
        errors: Rink key to the exception fetching its group raises.
    """
    serve = get_schedule.side_effect

    def fake(rinks: list[Rink], start: date, end: date) -> list[Event]:
        if error := next((errors[rink.key] for rink in rinks if rink.key in errors), None):
            raise error
        return serve(rinks, start, end)

    get_schedule.side_effect = fake


def _exit_code(out: Path) -> int:
    """Export one day and return the command's exit status.

    Args:
        out: Export output directory.
    """
    try:
        main(["--date", "2026-09-26", "--days", "1", "--out-dir", str(out)])
    except SystemExit as exc:
        return exc.code
    return 0


API_DOWN = httpx.ConnectError("connection refused")
NOT_JSON = json.JSONDecodeError("Expecting value", "<html>", 0)
OUR_BUG = KeyError("attributes")


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
                "short_name": "KCI",
                "code": "KCI",
                "area": "Northgate",
                "lat": 47.7063,
                "lng": -122.3252,
                "sheets": ["Starbucks Rink 1", "Smartsheet Rink 2", "VMFH Rink 3"],
            }
        ],
    }


def test_day_payloads_serializes_every_event_field() -> None:
    # WHEN: building one rink's payload for a single day with one event
    payloads = day_payloads([EVENT], "kraken", date(2026, 9, 26), date(2026, 9, 26), GENERATED_AT)

    # THEN: the file has its date, rink, timestamp and every event field with ISO times
    assert payloads == {
        date(2026, 9, 26): {
            "date": "2026-09-26",
            "rink": "kraken",
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


@pytest.mark.parametrize(
    ("end", "expected"),
    [
        (
            date(2026, 9, 29),
            {date(2026, 9, 26): ["1"], date(2026, 9, 27): [], date(2026, 9, 28): ["2"], date(2026, 9, 29): []},
        ),
        (date(2026, 9, 27), {date(2026, 9, 26): ["1"], date(2026, 9, 27): []}),
    ],
)
def test_day_payloads_groups_by_start_day_within_range(end: date, expected: dict[date, list[str]]) -> None:
    # WHEN: building payloads for events on the 26th and on the 28th running past midnight
    payloads = day_payloads([EVENT, LATER_EVENT], "kraken", date(2026, 9, 26), end, GENERATED_AT)

    # THEN: every day in range gets a payload, events land on their start day and out-of-range ones are dropped
    assert {day: [e["id"] for e in p["events"]] for day, p in payloads.items()} == expected


def test_main_fetches_each_source_account_once_for_inclusive_range(get_schedule: MagicMock, tmp_path: Path) -> None:
    # WHEN: exporting 14 days from a date
    main(["--date", "2026-09-26", "--days", "14", "--out-dir", str(tmp_path)])

    # THEN: rinks sharing a source account are fetched together, each group once, for the inclusive range
    assert sorted([r.key for r in c.args[0]] for c in get_schedule.call_args_list) == [
        ["kirkland", "renton", "snoqualmie"],
        ["kraken"],
        ["ova", "lynnwood"],
    ]
    assert {c.args[1:] for c in get_schedule.call_args_list} == {(date(2026, 9, 26), date(2026, 10, 9))}


@patch("searinks.export.today_pacific", return_value=date(2026, 9, 28))
def test_main_defaults_to_today_in_pacific(today_pacific: MagicMock, get_schedule: MagicMock, tmp_path: Path) -> None:
    # WHEN: exporting without a date, as CI does on UTC runners
    main(["--days", "2", "--out-dir", str(tmp_path)])

    # THEN: the range starts on the Pacific date, not the machine's
    assert {c.args[1:] for c in get_schedule.call_args_list} == {(date(2026, 9, 28), date(2026, 9, 29))}


def test_main_writes_rinks_and_one_file_per_rink_per_day(get_schedule: MagicMock, tmp_path: Path) -> None:
    # GIVEN: an output directory that doesn't exist yet
    out = tmp_path / "site" / "data"

    # WHEN: exporting two days
    main(["--date", "2026-09-26", "--days", "2", "--out-dir", str(out)])

    # THEN: rinks.json lists every rink and each rink gets a file per day, empty or not
    assert len(json.loads((out / "rinks.json").read_text())["rinks"]) == len(RINKS)
    assert _written(out) == sorted(f"2026-09-{d}/{key}.json" for d in (26, 27) for key in RINKS)
    assert _event_ids(out / "days" / "2026-09-26" / "kraken.json") == ["1"]
    assert _event_ids(out / "days" / "2026-09-27" / "kraken.json") == []


def test_main_only_exports_requested_rinks(get_schedule: MagicMock, tmp_path: Path) -> None:
    # WHEN: refreshing just Kraken for one day
    main(["--rink", "kraken", "--date", "2026-09-26", "--days", "1", "--out-dir", str(tmp_path)])

    # THEN: only Kraken is fetched and written
    get_schedule.assert_called_once_with([KRAKEN], date(2026, 9, 26), date(2026, 9, 26))
    assert _written(tmp_path) == ["2026-09-26/kraken.json"]


def test_main_leaves_files_outside_range_untouched(get_schedule: MagicMock, tmp_path: Path) -> None:
    # GIVEN: a previously exported day outside the range being refreshed
    previous = tmp_path / "days" / "2026-09-25" / "kraken.json"
    previous.parent.mkdir(parents=True)
    previous.write_text("previous")

    # WHEN: refreshing a single later day
    main(["--date", "2026-09-26", "--days", "1", "--out-dir", str(tmp_path)])

    # THEN: the earlier day's file is left as it was
    assert previous.read_text() == "previous"


@pytest.mark.parametrize(
    ("error", "event", "expected_code", "expected_counts"),
    [
        (API_DOWN, "rinks_upstream_failed", 0, (len(RINKS) - 3, 3, 0)),
        (NOT_JSON, "rinks_upstream_failed", 0, (len(RINKS) - 3, 3, 0)),
        (OUR_BUG, "rinks_export_failed", 1, (len(RINKS) - 3, 0, 3)),
    ],
)
def test_main_keeps_exporting_when_a_rink_fails(
    get_schedule: MagicMock,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
    event: str,
    expected_code: int,
    expected_counts: tuple[int, int, int],
) -> None:
    # GIVEN: fetching Renton's source account raises and Renton has a previous export for the day
    _fail(get_schedule, {"renton": error})
    previous = tmp_path / "days" / "2026-09-26" / "renton.json"
    previous.parent.mkdir(parents=True)
    previous.write_text("previous")
    caplog.set_level(logging.INFO)

    # WHEN: exporting one day
    code = _exit_code(tmp_path)

    # THEN: every rink on that account fails together, Renton's previous file is kept, other accounts are
    # written, and the failure is logged once and classified
    sno_king = ["kirkland", "renton", "snoqualmie"]
    assert _written(tmp_path) == sorted(f"2026-09-26/{key}.json" for key in RINKS if key not in sno_king or key == "renton")
    assert previous.read_text() == "previous"
    assert [(r.levelname, r.rinks) for r in caplog.records if r.message == event] == [("ERROR", sno_king)]
    finished = next(r for r in caplog.records if r.message == "export_finished")
    assert (finished.succeeded, finished.upstream_failed, finished.internal_failed) == expected_counts
    assert code == expected_code


@pytest.mark.parametrize(
    ("errors", "expected_code"),
    [
        ({key: API_DOWN for key in RINKS}, 2),
        ({key: NOT_JSON if key == "ova" else API_DOWN for key in RINKS}, 2),
        ({key: OUR_BUG if key == "ova" else API_DOWN for key in RINKS}, 1),
        ({key: OUR_BUG for key in RINKS}, 1),
    ],
)
def test_main_exit_code_separates_api_outage_from_our_errors(
    get_schedule: MagicMock, tmp_path: Path, errors: dict[str, Exception], expected_code: int
) -> None:
    # GIVEN: every rink fails, from the API, from our side, or a mix
    _fail(get_schedule, errors)

    # WHEN: exporting one day
    code = _exit_code(tmp_path)

    # THEN: an all-API outage exits 2, and any error on our side exits 1
    assert code == expected_code
