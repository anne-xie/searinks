import argparse
import json
import logging
from collections.abc import Sequence
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from searinks.logs import configure_logging
from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rinks.registry import RINKS
from searinks.schedule import get_all_schedules

logger = logging.getLogger(__name__)


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


def day_payloads(events: Sequence[Event], start: date, end: date, generated_at: datetime) -> dict[date, dict]:
    """Build one `days/<date>.json` document per day from `start` to `end`.

    Every day in the range gets a document, empty or not, so the site can tell
    a day with no events from one that was never exported. Events belong to the
    day they start on; events outside the range are dropped.

    Args:
        events: Events to include, already sorted.
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
            "generated_at": generated_at.isoformat(),
            "events": [_event_dict(event) for event in day_events],
        }
        for day, day_events in by_day.items()
    }


def main(argv: list[str] | None = None) -> None:
    """Write every rink's unfiltered schedule for the static site, one file per day.

    Only days in the requested range are rewritten, so a single day can be
    refreshed without touching the rest.

    Args:
        argv: Command-line arguments; defaults to `sys.argv[1:]`.
    """
    parser = argparse.ArgumentParser(prog="searinks-export", description="Export all rink schedules as JSON")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="first day (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=14, help="number of days to export")
    parser.add_argument("--out-dir", type=Path, default=Path("site/data"), help="output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug details to stderr")
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    end = args.date + timedelta(days=args.days - 1)
    events = get_all_schedules(args.date, end)
    generated_at = datetime.now(ZoneInfo("America/Los_Angeles"))

    days_dir = args.out_dir / "days"
    days_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "rinks.json").write_text(json.dumps(rinks_payload(list(RINKS.values()), generated_at), indent=1))
    payloads = day_payloads(events, args.date, end, generated_at)
    for day, payload in payloads.items():
        (days_dir / f"{day.isoformat()}.json").write_text(json.dumps(payload, indent=1))
    logger.info("export_written", extra={"dir": str(args.out_dir), "days": len(payloads), "events": len(events)})
