from collections.abc import Sequence

from searinks.models.event import Event


def filter_events(
    events: Sequence[Event],
    *,
    search: str | None = None,
    drop_in: bool = False,
    sport: str | None = None,
) -> list[Event]:
    """Return the events matching every given filter, in their original order.

    Args:
        events: Events to narrow.
        search: Case-insensitive substring the title must contain.
        drop_in: Only keep sessions sold per visit.
        sport: Only keep events in this discipline ("hockey", "figure", "public").
    """
    return [
        e
        for e in events
        if (not search or search.lower() in e.title.lower())
        and (not drop_in or e.drop_in)
        and (not sport or e.discipline == sport)
    ]
