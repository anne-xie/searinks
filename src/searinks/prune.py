import argparse
import logging
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from searinks.clock import today_pacific
from searinks.logs import configure_logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PruneResult:
    """Counts from one prune run.

    Args:
        pruned: Past day folders removed.
        skipped: Entries under `days/` left alone because they aren't dates.
        failed: Past day folders that couldn't be removed.
    """

    pruned: int
    skipped: int
    failed: int


def prune_days(out_dir: Path, today: date) -> PruneResult:
    """Delete `days/<date>/` folders for dates before `today`.

    Args:
        out_dir: Export output directory holding `days/`.
        today: First date to keep.
    """
    pruned = skipped = failed = 0
    days_dir = out_dir / "days"
    for entry in sorted(days_dir.iterdir()) if days_dir.is_dir() else []:
        try:
            day = date.fromisoformat(entry.name)
        except ValueError:
            logger.warning("day_prune_skipped", extra={"entry": entry.name})
            skipped += 1
            continue
        if day >= today:
            continue
        try:
            shutil.rmtree(entry)
        except OSError:
            logger.exception("day_prune_failed", extra={"date": entry.name})
            failed += 1
        else:
            logger.info("day_pruned", extra={"date": entry.name})
            pruned += 1
    return PruneResult(pruned=pruned, skipped=skipped, failed=failed)


def main(argv: list[str] | None = None) -> None:
    """Delete exported day files for dates that have passed. Exits 1 if any day couldn't be removed.

    Args:
        argv: Command-line arguments; defaults to `sys.argv[1:]`.
    """
    parser = argparse.ArgumentParser(prog="searinks-prune", description="Delete exported days before today")
    parser.add_argument("--out-dir", type=Path, default=Path("site/data"), help="export output directory")
    parser.add_argument("--today", type=date.fromisoformat, help="first day to keep (default: today, Pacific)")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug details to stderr")
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    today = args.today or today_pacific()
    logger.info("prune_started", extra={"out_dir": str(args.out_dir), "today": today.isoformat()})
    result = prune_days(args.out_dir, today)
    logger.info("prune_finished", extra={"pruned": result.pruned, "skipped": result.skipped, "failed": result.failed})
    if result.failed:
        raise SystemExit(1)
