from __future__ import annotations

import pathlib

import pytest

from zulup import util_constants
from zulup.util_traverse_zulup import TraverseZulup

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata_zulup" / "top"


def test_traverse_finds_correct_backup_json() -> None:
    traverse = TraverseZulup()
    traverse.collect(DIRECTORY_TESTDATA)

    backup_names = sorted(
        entry.backup_json.backup_name for entry in traverse.list_dir_zulup_json
    )
    assert backup_names == ["project_rs", "project_xy"]


def test_traverse_finds_correct_directories() -> None:
    traverse = TraverseZulup()
    traverse.collect(DIRECTORY_TESTDATA)

    directories = sorted(entry.directory.name for entry in traverse.list_dir_zulup_json)
    assert directories == ["project_rs", "project_xy"]


def test_traverse_respects_depth_limit() -> None:
    traverse = TraverseZulup()
    traverse.collect(DIRECTORY_TESTDATA)

    # deep/ignored/zulup_backup.json must NOT be found due to top/zulup_scan.json
    assert len(traverse.list_dir_zulup_json) == 2


def test_get_zulup_entry_raises_for_unknown_backup_name() -> None:
    traverse = TraverseZulup()
    traverse.collect(DIRECTORY_TESTDATA)

    with pytest.raises(ValueError, match="Backup 'nonexistent' not found"):
        traverse.get_zulup_entry("nonexistent")


def test_collect_raises_when_backup_and_scan_json_coexist(
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / util_constants.ZULUP_BACKUP_JSON).write_text("{}")
    (tmp_path / util_constants.ZULUP_SCAN_JSON).write_text("{}")

    traverse = TraverseZulup()
    with pytest.raises(
        ValueError,
        match=f"'{util_constants.ZULUP_BACKUP_JSON}' and '{util_constants.ZULUP_SCAN_JSON}' must not coexist",
    ):
        traverse.collect(tmp_path)
