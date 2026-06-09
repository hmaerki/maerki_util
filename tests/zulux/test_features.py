from __future__ import annotations

import json
import pathlib

import pytest

from zulux.util_zulux import ZuluxTest

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


# ---------------------------------------------------------------------------
# Unit tests — inline assertions, no golden files needed
# ---------------------------------------------------------------------------


def test_prefixed_filename_accepted(tmp_path: pathlib.Path) -> None:
    """Any prefix before zulux_chmod.json in the filename must be accepted."""
    config = tmp_path / "A_zulux_chmod.json"
    config.write_text(json.dumps([{"files": {"patterns": [], "chmod": "::"}}]))
    zt = ZuluxTest(
        filename_zulux_chmod_json=config,
        filename_expected=tmp_path / "out.txt",
    )
    assert zt is not None


def test_invalid_filename_rejected(tmp_path: pathlib.Path) -> None:
    """A filename not ending with zulux_chmod.json must raise AssertionError."""
    config = tmp_path / "permissions.json"
    config.write_text(json.dumps([]))
    with pytest.raises(AssertionError):
        ZuluxTest(
            filename_zulux_chmod_json=config,
            filename_expected=tmp_path / "out.txt",
        )


def test_directory_self_applies_chmod(tmp_path: pathlib.Path) -> None:
    """apply_directory_self() applies directory_self chmod, written as './'."""
    config = tmp_path / "zulux_chmod.json"
    config.write_text(
        json.dumps([{"directory_self": {"chmod": "root:root:rwx------"}}])
    )
    expected = tmp_path / "expected.txt"
    zt = ZuluxTest(filename_zulux_chmod_json=config, filename_expected=expected)
    zt.apply_directory_self()
    zt.write_expected()
    assert expected.read_text() == "chown root:root ./\nchmod rwx------ ./\n"


def test_no_match_produces_no_output(tmp_path: pathlib.Path) -> None:
    """A file matching no patterns must produce no output entry."""
    config = tmp_path / "zulux_chmod.json"
    config.write_text(
        json.dumps([{"files": {"patterns": ["*.py"], "chmod": "a:b:rwx------"}}])
    )
    expected = tmp_path / "expected.txt"
    zt = ZuluxTest(filename_zulux_chmod_json=config, filename_expected=expected)
    zt.apply_file(pathlib.Path("README.md"))
    zt.write_expected()
    assert expected.read_text() == ""


def test_missing_patterns_key_treated_as_empty(tmp_path: pathlib.Path) -> None:
    """An entry missing the 'patterns' key behaves as an empty list (no matches)."""
    config = tmp_path / "zulux_chmod.json"
    config.write_text(json.dumps([{"files": {"chmod": "a:b:rwx------"}}]))
    expected = tmp_path / "expected.txt"
    zt = ZuluxTest(filename_zulux_chmod_json=config, filename_expected=expected)
    zt.apply_file(pathlib.Path("any.txt"))
    zt.write_expected()
    assert expected.read_text() == ""


def test_first_entry_wins_not_second(tmp_path: pathlib.Path) -> None:
    """When two entries both match, only the first entry is applied."""
    config = tmp_path / "zulux_chmod.json"
    config.write_text(
        json.dumps(
            [
                {"files": {"patterns": ["*.py"], "chmod": "first:first:rw-------"}},
                {"files": {"patterns": ["*.py"], "chmod": "second:second:rwxrwxrwx"}},
            ]
        )
    )
    expected = tmp_path / "expected.txt"
    zt = ZuluxTest(filename_zulux_chmod_json=config, filename_expected=expected)
    zt.apply_file(pathlib.Path("main.py"))
    zt.write_expected()
    assert (
        expected.read_text() == "chown first:first main.py\nchmod rw------- main.py\n"
    )


def test_directory_not_matched_by_files_section(tmp_path: pathlib.Path) -> None:
    """A directory path must not be matched by the 'files' section, and vice versa."""
    config = tmp_path / "zulux_chmod.json"
    config.write_text(
        json.dumps([{"files": {"patterns": ["*"], "chmod": "a:b:rwx------"}}])
    )
    expected = tmp_path / "expected.txt"
    zt = ZuluxTest(filename_zulux_chmod_json=config, filename_expected=expected)
    zt.apply_directory(pathlib.Path("docs"))  # files section must NOT match this
    zt.write_expected()
    assert expected.read_text() == ""
