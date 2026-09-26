from collections.abc import Iterable, Mapping

DISCIPLINES = ("hockey", "figure", "public")

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


def check_overrides(overrides: Mapping[str, str]) -> None:
    """Raise if any override maps to something other than a known discipline.

    Args:
        overrides: Rink-specific exact title to discipline.

    Raises:
        ValueError: Listing each offending title and value.
    """
    unknown = {title: value for title, value in overrides.items() if value not in DISCIPLINES}
    if unknown:
        raise ValueError(f"unknown disciplines in overrides {unknown}; expected one of {DISCIPLINES}")


def unmatched_overrides(overrides: Mapping[str, str], titles: Iterable[str]) -> list[str]:
    """Return overridden titles that appear nowhere in `titles`, sorted.

    Args:
        overrides: Rink-specific exact title to discipline.
        titles: Titles of the events fetched for the rink.
    """
    return sorted(set(overrides) - set(titles))
