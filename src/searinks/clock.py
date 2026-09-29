from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_pacific() -> date:
    """Return today's date in the rinks' timezone, whatever the machine's timezone is."""
    return datetime.now(ZoneInfo("America/Los_Angeles")).date()
