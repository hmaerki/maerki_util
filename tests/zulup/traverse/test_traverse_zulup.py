from __future__ import annotations

import pathlib

from zulup.util_traverse_zulup import TraverseZulup

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata_zulup" / "top"


def test_traverse_finds_correct_zulup_json() -> None:
    traverse = TraverseZulup()
    traverse.collect(DIRECTORY_TESTDATA)

    backup_names = sorted(
        entry.zulup_json.backup.backup_name
        for entry in traverse.list_zulup_json
        if entry.zulup_json.backup is not None
    )
    assert backup_names == ["project_rs", "project_xy"]


def test_traverse_finds_correct_directories() -> None:
    traverse = TraverseZulup()
    traverse.collect(DIRECTORY_TESTDATA)

    directories = sorted(entry.directory.name for entry in traverse.list_zulup_json)
    assert directories == ["project_rs", "project_xy"]


def test_traverse_respects_depth_limit() -> None:
    traverse = TraverseZulup()
    traverse.collect(DIRECTORY_TESTDATA)

    # deep/ignored/zulup.json must NOT be found due to depth: 1 in top/zulup.json
    assert len(traverse.list_zulup_json) == 2
