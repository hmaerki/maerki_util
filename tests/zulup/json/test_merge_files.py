from __future__ import annotations

from zulup.util_json_metafile import (
    CurrentFileEntries,
    CurrentFileEntry,
    EnumVerb,
    MetafileFileEntry,
)

SNAPSHOT_OLD = "2026-04-03_12-22-22"
SNAPSHOT_NEW = "2026-04-05_10-00-00"


def _last(path: str, size: int, modified: str) -> MetafileFileEntry:
    return MetafileFileEntry(
        path=path,
        size=size,
        modified=modified,
        verb=EnumVerb.ADDED,
        snapshot_datetime=SNAPSHOT_OLD,
    )


def _current(path: str, size: int, modified: str) -> CurrentFileEntry:
    return CurrentFileEntry(path=path, size=size, modified=modified)


def test_all_added_when_no_last() -> None:
    current = [
        _current("a.txt", 100, "2026-04-05_09-00-00.000"),
        _current("b.txt", 200, "2026-04-05_09-00-00.000"),
    ]
    result = CurrentFileEntries(current).merge_files([], SNAPSHOT_NEW)
    assert len(result) == 2
    assert all(e.verb == EnumVerb.ADDED for e in result)
    assert all(e.snapshot_datetime == SNAPSHOT_NEW for e in result)


def test_untouched_when_same_size_and_modified() -> None:
    last = [_last("a.txt", 100, "2026-04-03_09-00-00.000")]
    current = [_current("a.txt", 100, "2026-04-03_09-00-00.000")]
    result = CurrentFileEntries(current).merge_files(last, SNAPSHOT_NEW)
    assert len(result) == 1
    assert result[0].verb == EnumVerb.UNTOUCHED


def test_modified_when_size_changed() -> None:
    last = [_last("a.txt", 100, "2026-04-03_09-00-00.000")]
    current = [_current("a.txt", 150, "2026-04-03_09-00-00.000")]
    result = CurrentFileEntries(current).merge_files(last, SNAPSHOT_NEW)
    assert len(result) == 1
    assert result[0].verb == EnumVerb.MODIFIED


def test_modified_when_mtime_changed() -> None:
    last = [_last("a.txt", 100, "2026-04-03_09-00-00.000")]
    current = [_current("a.txt", 100, "2026-04-05_09-00-00.000")]
    result = CurrentFileEntries(current).merge_files(last, SNAPSHOT_NEW)
    assert len(result) == 1
    assert result[0].verb == EnumVerb.MODIFIED


def test_removed_when_file_gone() -> None:
    last = [_last("a.txt", 100, "2026-04-03_09-00-00.000")]
    result = CurrentFileEntries([]).merge_files(last, SNAPSHOT_NEW)
    assert len(result) == 1
    assert result[0].verb == EnumVerb.REMOVED
    assert result[0].path == "a.txt"


def test_mixed_verbs() -> None:
    last = [
        _last("keep.txt", 100, "2026-04-03_09-00-00.000"),
        _last("change.txt", 200, "2026-04-03_09-00-00.000"),
        _last("gone.txt", 300, "2026-04-03_09-00-00.000"),
    ]
    current = [
        _current("keep.txt", 100, "2026-04-03_09-00-00.000"),
        _current("change.txt", 250, "2026-04-05_09-00-00.000"),
        _current("new.txt", 400, "2026-04-05_09-00-00.000"),
    ]
    result = CurrentFileEntries(current).merge_files(last, SNAPSHOT_NEW)
    by_path = {e.path: e for e in result}
    assert by_path["keep.txt"].verb == EnumVerb.UNTOUCHED
    assert by_path["change.txt"].verb == EnumVerb.MODIFIED
    assert by_path["gone.txt"].verb == EnumVerb.REMOVED
    assert by_path["new.txt"].verb == EnumVerb.ADDED


def test_result_sorted_by_path() -> None:
    current = [
        _current("z.txt", 10, "2026-04-05_09-00-00.000"),
        _current("a.txt", 20, "2026-04-05_09-00-00.000"),
    ]
    result = CurrentFileEntries(current).merge_files([], SNAPSHOT_NEW)
    assert [e.path for e in result] == ["a.txt", "z.txt"]
