from __future__ import annotations

import pathlib

from zulup.util_traverse_zulup import TraverseZulup

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata_zulup" / "top"

_traverse = TraverseZulup()
_traverse.collect(DIRECTORY_TESTDATA)


def test_traverse_project_rs_files() -> None:
    backup = _traverse.get_traverse_backup("project_rs")
    assert backup.files == [
        "a.txt",
        "sub/b.txt",
    ]


def test_traverse_project_xy_files() -> None:
    backup = _traverse.get_traverse_backup("project_xy")
    assert backup.files == [
        "project_xy/README.md",
        "project_xy/sub/README.md",
        "project_xy/sub/main.c",
        "project_xy/sub/task.txt",
    ]


def test_traverse_project_xy_excludes_git() -> None:
    backup = _traverse.get_traverse_backup("project_xy")
    # sub/_git directory should be excluded by filter rule (nocase match for "_git")
    assert all("_git" not in f.lower() for f in backup.files)
