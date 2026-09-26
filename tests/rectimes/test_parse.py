import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from searinks.models.event import Event
from searinks.models.rink import Rink
from searinks.rectimes.parse import parse_bookings
from searinks.rectimes.source import RecTimesSource

PACIFIC = ZoneInfo("America/Los_Angeles")

RINK = Rink(
    key="test",
    name="Test Rink",
    short_name="Test",
    code="TST",
    area="Seattle",
    lat=47.6,
    lng=-122.3,
    timezone="America/Los_Angeles",
    source=RecTimesSource(
        facility="testfac",
        venues={10: "Main Rink", 11: "Studio"},
        drop_in_groups=frozenset({"Stick & Puck"}),
        discipline_overrides={"SJHA": "hockey"},
    ),
)


def _booking(
    booking_id: int,
    *,
    group_name: str = "Stick & Puck",
    event_name: str = "",
    venue_id: int = 10,
    hidden: bool = False,
    start: str = "2026-09-26T12:45:00",
    end: str = "2026-09-26T14:15:00",
) -> dict[str, Any]:
    """Build a RecTimes calendar booking.

    Args:
        booking_id: Booking id.
        group_name: Name of the group that booked the ice.
        event_name: Optional event name set on the booking.
        venue_id: RecTimes venue (ice sheet) id.
        hidden: Whether the booking is hidden from the public calendar.
        start: Local start timestamp.
        end: Local end timestamp.
    """
    return {
        "id": booking_id,
        "groupName": group_name,
        "eventName": event_name,
        "venueId": venue_id,
        "hiddenFromPublic": hidden,
        "eventTypeName": "Adult Game",
        "startTimeLocal": start,
        "endTimeLocal": end,
    }


def test_parse_bookings_reads_booking_fields() -> None:
    # GIVEN: a booking on the second venue
    body = [_booking(7, group_name="Stick & Puck", venue_id=11)]

    # WHEN: parsing the bookings
    events = parse_bookings(body, RINK)

    # THEN: the event carries its rink, venue sheet name, localized times and discipline, with no type or sport
    assert events == [
        Event(
            id="7",
            title="Stick & Puck",
            rink="test",
            sheet="Studio",
            start=datetime(2026, 9, 26, 12, 45, tzinfo=PACIFIC),
            end=datetime(2026, 9, 26, 14, 15, tzinfo=PACIFIC),
            drop_in=True,
            discipline="hockey",
        )
    ]


@pytest.mark.parametrize(
    ("group_name", "event_name", "expected"),
    [
        ("Kraken Hockey League", "", "Kraken Hockey League"),
        ("Arctic Foxes ", "", "Arctic Foxes"),
        ("SJHA", " Tryouts ", "Tryouts"),
    ],
)
def test_parse_bookings_title_prefers_event_name_then_group(group_name: str, event_name: str, expected: str) -> None:
    # GIVEN: a booking with the given group and event names
    body = [_booking(1, group_name=group_name, event_name=event_name)]

    # WHEN: parsing the bookings
    (parsed,) = parse_bookings(body, RINK)

    # THEN: the title falls back from event name to group name
    assert parsed.title == expected


@pytest.mark.parametrize(
    ("group_name", "discipline"),
    [
        ("SJHA", "hockey"),
        ("OVA Freestyle", "figure"),
        ("Arctic Foxes", None),
    ],
)
def test_parse_bookings_resolves_discipline_with_rink_overrides(group_name: str, discipline: str | None) -> None:
    # GIVEN: a booking by the given group at a rink that overrides "SJHA"
    body = [_booking(1, group_name=group_name)]

    # WHEN: parsing the bookings
    (parsed,) = parse_bookings(body, RINK)

    # THEN: the rink's override applies, and other titles fall back to the shared keywords
    assert parsed.discipline == discipline


@pytest.mark.parametrize(
    ("group_name", "drop_in"),
    [
        ("Stick & Puck", True),
        ("Stick & Puck ", True),
        ("SJHA STICK & PUCK", False),
        ("Kraken Hockey League", False),
    ],
)
def test_parse_bookings_marks_configured_groups_as_drop_in(group_name: str, drop_in: bool) -> None:
    # GIVEN: a booking by the given group
    body = [_booking(1, group_name=group_name)]

    # WHEN: parsing the bookings
    (parsed,) = parse_bookings(body, RINK)

    # THEN: only the rink's drop-in groups count
    assert parsed.drop_in is drop_in


@pytest.mark.parametrize(
    ("venue_id", "hidden", "kept"),
    [
        (10, False, True),
        (10, True, False),
        (99, False, False),
    ],
)
def test_parse_bookings_keeps_only_public_bookings_on_configured_venues(venue_id: int, hidden: bool, kept: bool) -> None:
    # GIVEN: a booking on the given venue with the given visibility
    body = [_booking(1, venue_id=venue_id, hidden=hidden)]

    # WHEN: parsing the bookings
    events = parse_bookings(body, RINK)

    # THEN: only public bookings on configured venues survive
    assert (len(events) == 1) is kept


def test_parse_bookings_logs_nothing_for_expected_bookings(caplog: pytest.LogCaptureFixture) -> None:
    # GIVEN: an ordinary booking and a hidden one on another venue
    body = [_booking(1), _booking(2, venue_id=99, hidden=True)]
    caplog.set_level(logging.DEBUG)

    # WHEN: parsing the bookings
    parse_bookings(body, RINK)

    # THEN: nothing is logged
    assert caplog.records == []


@pytest.mark.parametrize(
    ("booking", "message"),
    [
        (_booking(1, venue_id=99), "rectimes_booking_unknown_venue"),
        (_booking(1, group_name=" ", event_name=""), "rectimes_booking_untitled"),
    ],
)
def test_parse_bookings_warns_on_unexpected_bookings(
    caplog: pytest.LogCaptureFixture, booking: dict[str, Any], message: str
) -> None:
    # GIVEN: a public booking that is off the rink's venues or has no name
    caplog.set_level(logging.WARNING)

    # WHEN: parsing the bookings
    parse_bookings([booking], RINK)

    # THEN: one warning names the rink and booking
    (record,) = caplog.records
    assert (record.levelname, record.message, record.rink, record.booking_id) == ("WARNING", message, "test", 1)


def test_parse_bookings_skips_and_warns_on_malformed_bookings(caplog: pytest.LogCaptureFixture) -> None:
    # GIVEN: a booking missing its start time, next to a good one
    malformed = _booking(1)
    del malformed["startTimeLocal"]
    caplog.set_level(logging.WARNING)

    # WHEN: parsing the bookings
    events = parse_bookings([malformed, _booking(2)], RINK)

    # THEN: the malformed booking is dropped with a warning and the good one is kept
    assert [e.id for e in events] == ["2"]
    (record,) = caplog.records
    assert (record.message, record.rink, record.booking_id) == ("rectimes_booking_malformed", "test", 1)
    assert "startTimeLocal" in record.error
