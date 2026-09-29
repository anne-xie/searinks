import logging
import shutil
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from searinks.prune import PruneResult, main, prune_days

TODAY = date(2026, 9, 28)


@pytest.fixture(autouse=True)
def configure_logging() -> MagicMock:
    """Patch logging setup so prune runs don't change log levels for other tests."""
    with patch("searinks.prune.configure_logging") as mock:
        yield mock


def _tree(out_dir: Path, names: list[str]) -> Path:
    """Create `days/<name>/kraken.json` for each name.

    Args:
        out_dir: Export output directory.
        names: Entry names under `days/`.
    """
    days = out_dir / "days"
    for name in names:
        (days / name).mkdir(parents=True)
        (days / name / "kraken.json").write_text("{}")
    return days


def test_prune_days_removes_past_days_only(tmp_path: Path) -> None:
    # GIVEN: day folders from before, on and after today
    days = _tree(tmp_path, ["2026-09-26", "2026-09-27", "2026-09-28", "2026-09-29"])

    # WHEN: pruning
    result = prune_days(tmp_path, TODAY)

    # THEN: only past days are gone, today and later are untouched
    assert sorted(p.name for p in days.iterdir()) == ["2026-09-28", "2026-09-29"]
    assert result == PruneResult(pruned=2, skipped=0, failed=0)


@pytest.mark.parametrize("name", ["notes", "2026-13-01", "2026-9-1x"])
def test_prune_days_leaves_non_date_entries(tmp_path: Path, name: str, caplog: pytest.LogCaptureFixture) -> None:
    # GIVEN: an entry under days/ that isn't a YYYY-MM-DD date
    days = _tree(tmp_path, [name, "2026-09-01"])

    # WHEN: pruning
    with caplog.at_level(logging.WARNING, logger="searinks"):
        result = prune_days(tmp_path, TODAY)

    # THEN: it's kept and logged, while the past date is still removed
    assert [p.name for p in days.iterdir()] == [name]
    assert result == PruneResult(pruned=1, skipped=1, failed=0)
    assert [(r.message, r.entry) for r in caplog.records] == [("day_prune_skipped", name)]


def test_prune_days_without_days_dir_does_nothing(tmp_path: Path) -> None:
    # WHEN: pruning an output directory that has never been exported to
    result = prune_days(tmp_path, TODAY)

    # THEN: nothing fails
    assert result == PruneResult(pruned=0, skipped=0, failed=0)


def test_prune_days_keeps_going_after_a_failure(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    # GIVEN: two past days, the first of which can't be deleted
    days = _tree(tmp_path, ["2026-09-01", "2026-09-02"])
    real_rmtree = shutil.rmtree

    def flaky_rmtree(path: Path) -> None:
        if path.name == "2026-09-01":
            raise PermissionError("read-only")
        real_rmtree(path)

    # WHEN: pruning
    with patch("searinks.prune.shutil.rmtree", side_effect=flaky_rmtree), caplog.at_level(logging.ERROR, "searinks"):
        result = prune_days(tmp_path, TODAY)

    # THEN: the failure is logged with its traceback and the other day is still removed
    assert [p.name for p in days.iterdir()] == ["2026-09-01"]
    assert result == PruneResult(pruned=1, skipped=0, failed=1)
    assert [(r.message, r.date, r.exc_info is not None) for r in caplog.records] == [
        ("day_prune_failed", "2026-09-01", True)
    ]


@patch("searinks.prune.prune_days", return_value=PruneResult(pruned=3, skipped=0, failed=0))
def test_main_prunes_out_dir_before_given_date(prune: MagicMock, tmp_path: Path) -> None:
    # WHEN: running with an explicit output directory and date
    main(["--out-dir", str(tmp_path), "--today", "2026-09-28"])

    # THEN: that directory is pruned as of that date
    prune.assert_called_once_with(tmp_path, TODAY)


@patch("searinks.prune.prune_days", return_value=PruneResult(pruned=0, skipped=0, failed=1))
def test_main_exits_1_when_a_day_failed(prune: MagicMock, tmp_path: Path) -> None:
    # WHEN/THEN: any failed day makes the run fail so CI notices
    with pytest.raises(SystemExit) as exit_info:
        main(["--out-dir", str(tmp_path), "--today", "2026-09-28"])
    assert exit_info.value.code == 1


@patch("searinks.prune.prune_days", return_value=PruneResult(pruned=0, skipped=0, failed=0))
@patch("searinks.prune.today_pacific", return_value=TODAY)
def test_main_defaults_to_today_in_pacific(today_pacific: MagicMock, prune: MagicMock) -> None:
    # WHEN: running without a date, as CI does on UTC runners
    main([])

    # THEN: "today" is the Pacific date and the export's default directory is used
    prune.assert_called_once_with(Path("site/data"), TODAY)
