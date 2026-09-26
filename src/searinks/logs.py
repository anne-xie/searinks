import logging
import sys

_RECORD_FIELDS = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime"}


class KeyValueFormatter(logging.Formatter):
    """Formats records as `LEVEL logger event key=value ...` from the fields passed in `extra`."""

    def format(self, record: logging.LogRecord) -> str:
        """Render one record.

        Args:
            record: Record to render.
        """
        line = f"{record.levelname} {record.name} {record.getMessage()}"
        for key, value in vars(record).items():
            if key not in _RECORD_FIELDS:
                line += f" {key}={value!r}" if isinstance(value, str) and " " in value else f" {key}={value}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


def configure_logging(verbose: bool) -> None:
    """Send log records to stderr as key=value lines; third-party loggers stay at warnings.

    Args:
        verbose: Include searinks debug records, e.g. overrides that matched no event.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(KeyValueFormatter())
    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    logging.getLogger("searinks").setLevel(logging.DEBUG if verbose else logging.WARNING)
