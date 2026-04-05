from __future__ import annotations

import pathlib

from zulup.util_traverse_backup import TraverseBackup
from zulup.util_traverse_zulup import TraverseZulup

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata_zulup" / "top"


def _get_entry(backup_name: str) -> TraverseBackup:
    traverse = TraverseZulup(DIRECTORY_TESTDATA)
    for entry in traverse.backups:
        assert entry.zulup_json.backup is not None
        if entry.zulup_json.backup.backup_name == backup_name:
            return TraverseBackup(entry)
    raise AssertionError(f"Backup '{backup_name}' not found")


def test_traverse_project_rs_files() -> None:
    backup = _get_entry("project_rs")
    assert backup.files == [
        "a.txt",
        "sub/b.txt",
    ]


def test_traverse_project_xy_files() -> None:
    backup = _get_entry("project_xy")
    assert backup.files == [
        "project_xy/README.md",
        "project_xy/sub/README.md",
        "project_xy/sub/main.c",
        "project_xy/sub/task.txt",
    ]


def test_traverse_project_xy_excludes_git() -> None:
    backup = _get_entry("project_xy")
    # sub/_git directory should be excluded by filter rule (nocase match for "_git")
    assert all("_git" not in f.lower() for f in backup.files)
