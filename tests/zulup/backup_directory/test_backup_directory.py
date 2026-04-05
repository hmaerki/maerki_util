from __future__ import annotations

import pathlib

import pytest

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
    assert bd.last_snapshot is not None
    bd.verify_history(bd.last_snapshot.metafile)


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
    assert bd.last_snapshot is not None
    bd.verify_history(bd.last_snapshot.metafile)
    assert len(bd.last_snapshot.metafile.history) == 1


def test_metafile_and_tarfile_paths() -> None:
    bd = BackupDirectory(DIRECTORY_TESTDATA / "directory_full", BACKUP_NAME)
    entry = bd.snapshots[0]
    assert entry.filename_metafile.name == "project_xy_2026-04-03_12-22-22_full.json"


def test_ignores_other_backup_names() -> None:
    bd = BackupDirectory(DIRECTORY_TESTDATA / "directory_full", "other_project")
    assert bd.snapshots == []
    assert bd.last_snapshot is None


def test_verify_history_missing(tmp_path: pathlib.Path) -> None:
    """A metafile referencing a history snapshot that doesn't exist should raise."""
    metafile_content = {
        "backup": {
            "backup_name": "project_xy",
            "parent": "/tmp",
            "hostname": "test",
            "tar_checksum": "sha256:abc",
        },
        "current": {
            "snapshot_datetime": "2026-04-03_13-22-22",
            "snapshot_type": "incr",
            "snapshot_stem": "project_xy_2026-04-03_13-22-22_incr",
        },
        "history": [
            {
                "snapshot_datetime": "2026-04-03_12-22-22",
                "snapshot_type": "full",
                "snapshot_stem": "project_xy_2026-04-03_12-22-22_full",
                "tar_checksum": "sha256:def",
            }
        ],
        "files": [],
    }
    import json

    metafile_path = tmp_path / "project_xy_2026-04-03_13-22-22_incr.json"
    metafile_path.write_text(json.dumps(metafile_content))
    # No full metafile exists -> verify_history should raise
    bd = BackupDirectory(tmp_path, "project_xy")
    assert bd.last_snapshot is not None
    with pytest.raises(ValueError, match="Missing metafile"):
        bd.verify_history(bd.last_snapshot.metafile)
