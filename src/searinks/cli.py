import argparse
from datetime import date, timedelta

from searinks.daysmart import DaySmartClient
from searinks.models import Event
from searinks.rinks import RINKS


def main(argv: list[str] | None = None) -> None:
    """Print a rink's schedule.

    Args:
        argv: Command-line arguments; defaults to `sys.argv[1:]`.
    """
    parser = argparse.ArgumentParser(prog="searinks", description="Ice rink schedules from DaySmart")
    parser.add_argument("rink", choices=sorted(RINKS), help="rink to query")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="first day (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=1, help="number of days to show")
    parser.add_argument("--search", help="case-insensitive title filter, e.g. 'stick'")
    parser.add_argument("--drop-in", action="store_true", help="only sessions sold per visit")
    parser.add_argument("--sport", choices=["hockey", "figure", "public"], help="only this discipline")
    args = parser.parse_args(argv)

    rink = RINKS[args.rink]
    events = DaySmartClient(rink).get_events(args.date, args.date + timedelta(days=args.days - 1))
    if args.search:
        events = [e for e in events if args.search.lower() in e.title.lower()]
    if args.drop_in:
        events = [e for e in events if e.drop_in]
    if args.sport:
        events = [e for e in events if e.discipline == args.sport]

    print(rink.name)
    current_day = None
    for event in events:
        if event.start.date() != current_day:
            current_day = event.start.date()
            print(f"\n{event.start:%a %b %d}")
        print(_format(event))


def _format(event: Event) -> str:
    """Render one event as a table row.

    Args:
        event: Event to render.
    """
    slots = f"  ({event.open_slots}/{event.capacity} open)" if event.capacity else ""
    return f"  {event.start:%H:%M}-{event.end:%H:%M}  {event.sheet:<18}  {event.title}{slots}"
