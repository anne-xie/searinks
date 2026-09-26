DISCIPLINE_KEYWORDS = {
    "hockey": ("hockey",),
    "figure": ("freestyle", "fs ", "figure", "dance"),
    "public": ("public skate",),
}


def discipline_for(sport: str | None, title: str) -> str | None:
    """Group an event into "hockey", "figure" or "public".

    Args:
        sport: Sport name as configured by the rink, e.g. "Open Freestyle".
        title: Event title; used to spot public skates at rinks that file
            them under a generic sport like "Ice Skating".

    Returns:
        The discipline, or None when the event doesn't clearly belong to one.
    """
    if sport and "public skate" in title.lower():
        return "public"
    name = f"{sport or ''} ".lower()
    for discipline, keywords in DISCIPLINE_KEYWORDS.items():
        if any(k in name for k in keywords):
            return discipline
    return None
