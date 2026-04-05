from __future__ import annotations

import pathlib

from zulup.util_backup_directory import BackupDirectory

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata"

BACKUP_NAME = "project_xy"


def test_empty_directory() -> None:
    bd = BackupDirectory(DIRECTORY_TESTDATA / "directory_empty", BACKUP_NAME)
    assert bd.snapshots == []
    assert bd.last_snapshot is None


def test_full_only() -> None:
    bd = BackupDirectory(DIRECTORY_TESTDATA / "directory_full", BACKUP_NAME)
    assert len(bd.snapshots) == 1
    entry = bd.snapshots[0]
    assert entry.filename_metafile.name == "project_xy_2026-04-03_12-22-22_full.json"
    assert bd.last_snapshot == entry


def test_full_and_incr() -> None:
    bd = BackupDirectory(DIRECTORY_TESTDATA / "directory_incr", BACKUP_NAME)
    assert len(bd.snapshots) == 2
    assert (
        bd.snapshots[0].filename_metafile.name
        == "project_xy_2026-04-03_12-22-22_full.json"
    )
    assert (
        bd.snapshots[1].filename_metafile.name
        == "project_xy_2026-04-03_13-22-22_incr.json"
    )
    assert bd.last_snapshot == bd.snapshots[1]


def test_metafile_and_tarfile_paths() -> None:
    bd = BackupDirectory(DIRECTORY_TESTDATA / "directory_full", BACKUP_NAME)
    entry = bd.snapshots[0]
    assert entry.filename_metafile.name == "project_xy_2026-04-03_12-22-22_full.json"


def test_ignores_other_backup_names() -> None:
    bd = BackupDirectory(DIRECTORY_TESTDATA / "directory_full", "other_project")
    assert bd.snapshots == []
    assert bd.last_snapshot is None
