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


def test_missing_patterns_key_is_catch_all() -> None:
    """An entry missing the 'patterns' key matches any file (catch-all default)."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[{"files": {"chmod": "a:b:rwx------"}}],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("any.txt"))
    assert (
        f.getvalue()
        == "chown a:b                any.txt\nchmod rwx------          any.txt\n"
    )


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
        == "chown first:first        main.py\nchmod rw-------          main.py\n"
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


def test_exclude_pattern_suppresses_match() -> None:
    """A '!' pattern that matches a file must suppress it (return False)."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[
            {
                "files": {
                    "patterns": ["!secret.txt", "*.txt"],
                    "chmod": "a:b:rw-r--r--",
                }
            }
        ],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("secret.txt"))
    assert f.getvalue() == "", "excluded file must produce no output"


def test_exclude_pattern_does_not_suppress_non_matching_file() -> None:
    """A '!' pattern that does NOT match must leave other files unaffected."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[
            {
                "files": {
                    "patterns": ["!secret.txt", "*.txt"],
                    "chmod": "a:b:rw-r--r--",
                }
            }
        ],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("public.txt"))
    assert (
        f.getvalue()
        == "chown a:b                public.txt\nchmod rw-r--r--          public.txt\n"
    )


def test_exclude_pattern_by_path_suppresses_match() -> None:
    """A '!' pattern with a path component suppresses the exact path only."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[
            {
                "files": {
                    "patterns": ["!wikiwiki/secret.cgi", "wikiwiki/*.cgi"],
                    "chmod": "a:b:rwxrwx---",
                }
            }
        ],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("wikiwiki/secret.cgi"))
    assert f.getvalue() == "", "path-excluded file must produce no output"
    zt.apply_file(pathlib.Path("wikiwiki/run.cgi"))
    assert "wikiwiki/run.cgi" in f.getvalue(), "non-excluded .cgi must still match"


def test_exclude_directory_pattern_suppresses_match() -> None:
    """A '!dir/' pattern must suppress the named directory."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[
            {
                "directories": {
                    "patterns": ["!.git/", "*/"],
                    "chmod": "a:b:rwxr-xr-x",
                }
            }
        ],
        f_expected=f,
    )
    zt.apply_directory(pathlib.Path(".git"))
    assert f.getvalue() == "", "excluded directory must produce no output"
    zt.apply_directory(pathlib.Path("src"))
    assert "src" in f.getvalue(), "non-excluded directory must still match"


def test_leading_slash_anchors_to_top_level() -> None:
    """A pattern starting with '/' must only match files at the top level."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[{"files": {"patterns": ["/*.py"], "chmod": "a:b:rw-r--r--"}}],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("main.py"))
    assert "main.py" in f.getvalue(), "top-level file must match"
    zt.apply_file(pathlib.Path("sub/main.py"))
    assert "sub/main.py" not in f.getvalue(), "nested file must NOT match"


def test_plain_glob_matches_at_any_depth() -> None:
    """A pattern without '/' must match files at any depth."""
    f = io.StringIO()
    zt = ZuluxTest(
        zulux_json=[{"files": {"patterns": ["*.py"], "chmod": "a:b:rw-r--r--"}}],
        f_expected=f,
    )
    zt.apply_file(pathlib.Path("main.py"))
    zt.apply_file(pathlib.Path("sub/main.py"))
    assert f.getvalue().count("\n") == 4, "both files must match (2 lines each)"
