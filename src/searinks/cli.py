import argparse
from datetime import date, timedelta

from searinks.disciplines import DISCIPLINES
from searinks.filters import filter_events
from searinks.logs import configure_logging
from searinks.models.event import Event
from searinks.rinks.registry import RINKS
from searinks.schedule import get_all_schedules, get_schedule


def main(argv: list[str] | None = None) -> None:
    """Print the schedule for one or more rinks.

    Args:
        argv: Command-line arguments; defaults to `sys.argv[1:]`.
    """
    parser = argparse.ArgumentParser(prog="searinks", description="Seattle-area ice rink schedules")
    parser.add_argument(
        "rinks",
        nargs="*",
        choices=sorted(RINKS),
        metavar="rink",
        help=f"rinks to query (default: all): {', '.join(sorted(RINKS))}",
    )
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="first day (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=1, help="number of days to show")
    parser.add_argument("--search", help="case-insensitive title filter, e.g. 'stick'")
    parser.add_argument("--drop-in", action="store_true", help="only sessions sold per visit")
    parser.add_argument("--sport", choices=DISCIPLINES, help="only this discipline")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug details to stderr")
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    end = args.date + timedelta(days=args.days - 1)
    if args.rinks:
        rinks = [RINKS[key] for key in dict.fromkeys(args.rinks)]
        events = get_schedule(rinks, args.date, end)
    else:
        rinks = list(RINKS.values())
        events = get_all_schedules(args.date, end)
    events = filter_events(events, search=args.search, drop_in=args.drop_in, sport=args.sport)

    names = {rink.key: rink.name for rink in rinks}
    rink_width = max(map(len, names.values())) if len(rinks) > 1 else 0
    print(", ".join(names.values()))
    current_day = None
    for event in events:
        if event.start.date() != current_day:
            current_day = event.start.date()
            print(f"\n{event.start:%a %b %d}")
        print(_format(event, names[event.rink], rink_width))


def _format(event: Event, rink_name: str, rink_width: int) -> str:
    """Render one event as a table row.

    Args:
        event: Event to render.
        rink_name: Display name of the event's rink.
        rink_width: Width of the rink column; 0 omits it.
    """
    rink = f"{rink_name:<{rink_width}}  " if rink_width else ""
    slots = f"  ({event.open_slots}/{event.capacity} open)" if event.capacity else ""
    return f"  {event.start:%H:%M}-{event.end:%H:%M}  {rink}{event.sheet:<18}  {event.title}{slots}"
