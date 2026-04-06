from __future__ import annotations

import json
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
        "README.md",
        "sub/README.md",
        "sub/main.c",
        "sub/task.txt",
    ]


def test_traverse_project_xy_excludes_git() -> None:
    backup = _traverse.get_traverse_backup("project_xy")
    # sub/_git directory should be excluded by ignore rule
    assert all("_git" not in f.lower() for f in backup.files)


def test_ignore_dot_git_directories_recursively(tmp_path: pathlib.Path) -> None:
    project_dir = tmp_path / "project_demo"
    project_dir.mkdir()
    (project_dir / "keep.txt").write_text("ok")

    # Top-level .git directory
    dot_git_top = project_dir / ".git"
    dot_git_top.mkdir()
    (dot_git_top / "HEAD").write_text("ref: refs/heads/main\n")

    # Nested .git directory
    nested_dir = project_dir / "src"
    nested_dir.mkdir()
    (nested_dir / "code.py").write_text("print('ok')\n")
    dot_git_nested = nested_dir / ".git"
    dot_git_nested.mkdir()
    (dot_git_nested / "config").write_text("[core]\n")

    zulup_json = {
        "backup": {
            "backup_name": "project_demo",
            "directory_target": "/tmp/backup",
            "directory_src": ".",
            "directory_name_include": False,
            "ignore": [".git/"],
        }
    }
    (project_dir / "zulup.json").write_text(json.dumps(zulup_json, indent=4) + "\n")

    traverse = TraverseZulup()
    traverse.collect(project_dir)

    backup = traverse.get_traverse_backup("project_demo")
    assert backup.files == ["keep.txt", "src/code.py"]
