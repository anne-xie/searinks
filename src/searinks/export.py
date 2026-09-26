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


def to_payload(events: Sequence[Event], rinks: Sequence[Rink], generated_at: datetime) -> dict:
    """Build the JSON document the static site reads.

    Args:
        events: Events to include, already sorted.
        rinks: Rinks to list with their display metadata.
        generated_at: When the data was fetched.
    """

    def event_dict(event: Event) -> dict:
        """Serialize one event with ISO timestamps.

        Args:
            event: Event to serialize.
        """
        return asdict(event) | {"start": event.start.isoformat(), "end": event.end.isoformat()}

    def rink_dict(rink: Rink) -> dict:
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

    return {
        "generated_at": generated_at.isoformat(),
        "rinks": [rink_dict(rink) for rink in rinks],
        "events": [event_dict(event) for event in events],
    }


def main(argv: list[str] | None = None) -> None:
    """Write every rink's unfiltered schedule to a JSON file for the static site.

    Args:
        argv: Command-line arguments; defaults to `sys.argv[1:]`.
    """
    parser = argparse.ArgumentParser(prog="searinks-export", description="Export all rink schedules as JSON")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="first day (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=14, help="number of days to export")
    parser.add_argument("--out", type=Path, default=Path("site/events.json"), help="output file")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug details to stderr")
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    end = args.date + timedelta(days=args.days - 1)
    events = get_all_schedules(args.date, end)
    payload = to_payload(events, list(RINKS.values()), datetime.now(ZoneInfo("America/Los_Angeles")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    logger.info("export_written", extra={"path": str(args.out), "events": len(events)})
