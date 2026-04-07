from __future__ import annotations

import pathlib

from zulup.util_pytest import TestProjectDirectory
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
        "README.md",
        "sub/README.md",
        "sub/main.c",
        "sub/task.txt",
    ]


def test_traverse_project_xy_excludes_git() -> None:
    backup = _traverse.get_traverse_backup("project_xy")
    # sub/_git directory should be excluded by ignore rule
    assert all("_git" not in f.lower() for f in backup.files)


def test_ignore_dot_git_directories_recursively(project: TestProjectDirectory) -> None:
    project.create_file("keep.txt", "ok")

    # Top-level .git directory
    project.create_file(".git/HEAD", "ref: refs/heads/main\n")

    # Nested .git directory
    project.create_file("src/code.py", "print('ok')\n")
    project.create_file("src/.git/config", "[core]\n")

    project.create_backup_json(directory_name_include=False, ignore=[".git/"])

    backup = project.get_traverse_backup()
    assert backup.files == ["keep.txt", "src/code.py"]
