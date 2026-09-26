from collections.abc import Mapping

DISCIPLINE_KEYWORDS = {
    "hockey": ("hockey", "puck"),
    "figure": ("freestyle", "fs ", "figure", "dance"),
    "public": ("public skate",),
}


def discipline_for(sport: str | None, title: str, overrides: Mapping[str, str] | None = None) -> str | None:
    """Group an event into "hockey", "figure" or "public".

    Args:
        sport: Sport name as configured by the rink, e.g. "Open Freestyle".
        title: Event title; used to spot public skates at rinks that file
            them under a generic sport like "Ice Skating", and matched in
            place of `sport` when there is none.
        overrides: Rink-specific exact title to discipline, checked before
            the shared keywords.

    Returns:
        The discipline, or None when the event doesn't clearly belong to one.
    """
    if overrides and title in overrides:
        return overrides[title]
    if "public skate" in title.lower():
        return "public"
    name = f"{sport or title} ".lower()
    for discipline, keywords in DISCIPLINE_KEYWORDS.items():
        if any(k in name for k in keywords):
            return discipline
    return None
