import logging
from unittest.mock import MagicMock, patch

import pytest

from searinks.logs import KeyValueFormatter, configure_logging


def _record(**extra: object) -> logging.LogRecord:
    """Build a warning record for `rectimes_booking_untitled` with extra fields.

    Args:
        extra: Fields passed through `extra={}`.
    """
    record = logging.LogRecord("searinks.rectimes.parse", logging.WARNING, __file__, 1, "rectimes_booking_untitled", None, None)
    record.__dict__.update(extra)
    return record


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        ({}, "WARNING searinks.rectimes.parse rectimes_booking_untitled"),
        (
            {"rink": "ova", "booking_id": 7},
            "WARNING searinks.rectimes.parse rectimes_booking_untitled rink=ova booking_id=7",
        ),
        ({"title": "Theater on Ice"}, "WARNING searinks.rectimes.parse rectimes_booking_untitled title='Theater on Ice'"),
    ],
)
def test_key_value_formatter_appends_extra_fields(extra: dict[str, object], expected: str) -> None:
    # WHEN/THEN: the event name is followed by each extra field as key=value, quoting values with spaces
    assert KeyValueFormatter().format(_record(**extra)) == expected


@pytest.fixture
def searinks_logger() -> logging.Logger:
    """Yield the `searinks` logger, restoring its level afterwards so other tests' log capture is unaffected."""
    logger = logging.getLogger("searinks")
    original = logger.level
    yield logger
    logger.setLevel(original)


@pytest.mark.parametrize(("verbose", "level"), [(False, logging.WARNING), (True, logging.DEBUG)])
@patch("searinks.logs.logging.basicConfig")
def test_configure_logging_sets_level_for_searinks_only(
    basic_config: MagicMock, searinks_logger: logging.Logger, verbose: bool, level: int
) -> None:
    # WHEN: configuring logging
    configure_logging(verbose=verbose)

    # THEN: the root logger stays at warnings with a key=value handler, and only searinks loggers follow `verbose`
    kwargs = basic_config.call_args.kwargs
    assert kwargs["level"] == logging.WARNING
    (handler,) = kwargs["handlers"]
    assert isinstance(handler.formatter, KeyValueFormatter)
    assert searinks_logger.level == level
