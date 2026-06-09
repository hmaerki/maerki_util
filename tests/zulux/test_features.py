from __future__ import annotations

import io
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
    zt = ZuluxTest(zulux_json=config, f_expected=io.StringIO())
    assert zt is not None


def test_invalid_filename_rejected(tmp_path: pathlib.Path) -> None:
    """A filename not ending with zulux_chmod.json must raise AssertionError."""
    config = tmp_path / "permissions.json"
    config.write_text(json.dumps([]))
    with pytest.raises(AssertionError):
        ZuluxTest(zulux_json=config, f_expected=io.StringIO())


def test_directory_self_applies_chmod() -> None:
    """apply_directory_self() applies directory_self chmod, written as './'."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[{"directory_self": {"chmod": "root:root:rwx------"}}],
        f_expected=f,
    )
    zt.apply_directory_self()
    assert f.getvalue() == "chown root:root          ./\nchmod rwx------          ./\n"


def test_no_match_produces_no_output() -> None:
    """A file matching no patterns must produce no output entry."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[{"files": {"patterns": ["*.py"], "chmod": "a:b:rwx------"}}],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("README.md"))
    assert f.getvalue() == ""


def test_missing_patterns_key_treated_as_empty() -> None:
    """An entry missing the 'patterns' key behaves as an empty list (no matches)."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[{"files": {"chmod": "a:b:rwx------"}}],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("any.txt"))
    assert f.getvalue() == ""


def test_first_entry_wins_not_second() -> None:
    """When two entries both match, only the first entry is applied."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[
            {"files": {"patterns": ["*.py"], "chmod": "first:first:rw-------"}},
            {"files": {"patterns": ["*.py"], "chmod": "second:second:rwxrwxrwx"}},
        ],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("main.py"))
    assert (
        f.getvalue()
        == "chown first:first        main.py/\nchmod rw-------          main.py/\n"
    )


def test_directory_not_matched_by_files_section() -> None:
    """A directory path must not be matched by the 'files' section, and vice versa."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[{"files": {"patterns": ["*"], "chmod": "a:b:rwx------"}}],
        f_expected=f,
    )
    zt.apply_directory(pathlib.Path("docs"))  # files section must NOT match this
    assert f.getvalue() == ""
