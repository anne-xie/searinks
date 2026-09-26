import argparse
import json
import logging
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import date, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from searinks.logs import configure_logging
from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rinks.registry import RINKS
from searinks.schedule import get_schedule

logger = logging.getLogger(__name__)

# Raised when a rink's schedule API is unreachable, errors or returns non-JSON.
UPSTREAM_ERRORS = (httpx.HTTPError, json.JSONDecodeError)


class RinkResult(StrEnum):
    """Outcome of exporting one rink."""

    OK = "ok"
    UPSTREAM_FAILED = "upstream_failed"
    INTERNAL_FAILED = "internal_failed"


def _event_dict(event: Event) -> dict:
    """Serialize one event with ISO timestamps.

    Args:
        event: Event to serialize.
    """
    return asdict(event) | {"start": event.start.isoformat(), "end": event.end.isoformat()}


def _rink_dict(rink: Rink) -> dict:
    """Serialize one rink's display metadata, leaving out its schedule source.

    Args:
        rink: Rink to serialize.
    """
    return {
        "key": rink.key,
        "name": rink.name,
        "short_name": rink.short_name,
        "code": rink.code,
        "area": rink.area,
        "lat": rink.lat,
        "lng": rink.lng,
        "sheets": rink.sheets,
    }


def rinks_payload(rinks: Sequence[Rink], generated_at: datetime) -> dict:
    """Build `rinks.json`, the rink list the static site reads once.

    Args:
        rinks: Rinks to list with their display metadata.
        generated_at: When the data was fetched.
    """
    return {"generated_at": generated_at.isoformat(), "rinks": [_rink_dict(rink) for rink in rinks]}


def day_payloads(
    events: Sequence[Event], rink: str, start: date, end: date, generated_at: datetime
) -> dict[date, dict]:
    """Build one rink's `days/<date>/<rink>.json` document per day from `start` to `end`.

    Every day in the range gets a document, empty or not, so the site can tell
    a day with no events from one that was never exported. Events belong to the
    day they start on; events outside the range are dropped.

    Args:
        events: The rink's events, already sorted.
        rink: Key of the rink the events are at.
        start: First day to include.
        end: Last day to include (inclusive).
        generated_at: When the data was fetched.
    """
    by_day: dict[date, list[Event]] = {start + timedelta(days=i): [] for i in range((end - start).days + 1)}
    for event in events:
        if (day := event.start.date()) in by_day:
            by_day[day].append(event)
    return {
        day: {
            "date": day.isoformat(),
            "rink": rink,
            "generated_at": generated_at.isoformat(),
            "events": [_event_dict(event) for event in day_events],
        }
        for day, day_events in by_day.items()
    }


def _export_rink(rink: Rink, start: date, end: date, out_dir: Path) -> RinkResult:
    """Fetch one rink and write its day files, logging instead of raising on failure.

    Args:
        rink: Rink to export.
        start: First day to include.
        end: Last day to include (inclusive).
        out_dir: Export output directory.
    """
    try:
        events = get_schedule([rink], start, end)
        payloads = day_payloads(events, rink.key, start, end, datetime.now(ZoneInfo("America/Los_Angeles")))
        for day, payload in payloads.items():
            path = out_dir / "days" / day.isoformat() / f"{rink.key}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=1))
    except UPSTREAM_ERRORS:
        logger.exception("rink_upstream_failed", extra={"rink": rink.key})
        return RinkResult.UPSTREAM_FAILED
    except Exception:
        logger.exception("rink_export_failed", extra={"rink": rink.key})
        return RinkResult.INTERNAL_FAILED
    logger.info("rink_exported", extra={"rink": rink.key, "events": len(events)})
    return RinkResult.OK


def main(argv: list[str] | None = None) -> None:
    """Write unfiltered schedules for the static site, one file per rink per day.

    Only the requested rinks and days are rewritten, and a rink that fails
    keeps its previous files. Exits 1 if any rink failed on our side, 2 if
    every rink's API failed, and 0 otherwise, including when only some APIs failed.

    Args:
        argv: Command-line arguments; defaults to `sys.argv[1:]`.
    """
    parser = argparse.ArgumentParser(prog="searinks-export", description="Export rink schedules as JSON")
    parser.add_argument(
        "--rink",
        action="append",
        choices=sorted(RINKS),
        help="rink to export; repeat for several (default: all)",
    )
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="first day (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=14, help="number of days to export")
    parser.add_argument("--out-dir", type=Path, default=Path("site/data"), help="output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug details to stderr")
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    rinks = [RINKS[key] for key in dict.fromkeys(args.rink)] if args.rink else list(RINKS.values())
    end = args.date + timedelta(days=args.days - 1)
    logger.info(
        "export_started",
        extra={"rinks": [r.key for r in rinks], "start": args.date.isoformat(), "end": end.isoformat()},
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(ZoneInfo("America/Los_Angeles"))
    (args.out_dir / "rinks.json").write_text(json.dumps(rinks_payload(list(RINKS.values()), generated_at), indent=1))
    with ThreadPoolExecutor(max_workers=len(rinks)) as pool:
        results = list(pool.map(lambda rink: _export_rink(rink, args.date, end, args.out_dir), rinks))

    counts = {result: results.count(result) for result in RinkResult}
    logger.info(
        "export_finished",
        extra={
            "succeeded": counts[RinkResult.OK],
            "upstream_failed": counts[RinkResult.UPSTREAM_FAILED],
            "internal_failed": counts[RinkResult.INTERNAL_FAILED],
        },
    )
    if counts[RinkResult.INTERNAL_FAILED]:
        raise SystemExit(1)
    if counts[RinkResult.UPSTREAM_FAILED] == len(results):
        raise SystemExit(2)
