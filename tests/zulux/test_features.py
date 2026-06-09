from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

from zulux.util_zulux import ZuluxTest

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


def _run_golden_test(test_name: str) -> None:
    """Apply ZuluxTest over all paths in <test_name>_input.txt and verify
    the output matches the committed golden file <test_name>_expected.txt.
    Input lines ending with '/' are treated as directories."""
    zt = ZuluxTest(
        filename_zulux_chmod_json=DIRECTORY_OF_THIS_FILE
        / f"{test_name}_zulux_chmod.json",
        filename_expected=DIRECTORY_OF_THIS_FILE / f"{test_name}_expected.txt",
    )
    input_file = DIRECTORY_OF_THIS_FILE / f"{test_name}_input.txt"
    for line in input_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith("/"):
            zt.apply_directory(pathlib.Path(line.rstrip("/")))
        else:
            zt.apply_file(pathlib.Path(line))
    zt.write_expected()

    result = subprocess.run(
        ["git", "diff", "--quiet", f"{test_name}_expected.txt"],
        cwd=DIRECTORY_OF_THIS_FILE,
    )
    assert result.returncode == 0, (
        f"{test_name}_expected.txt differs from committed version."
    )


# ---------------------------------------------------------------------------
# Golden-file tests — one per documented feature area
# ---------------------------------------------------------------------------


def test_b_directory_name_patterns() -> None:
    """Directories: name-only patterns with ! exclude (.git/ is excluded)."""
    _run_golden_test("test_b")


def test_c_directory_path_patterns() -> None:
    """Directories: path-based patterns and ! path exclude (build/output/ excluded)."""
    _run_golden_test("test_c")


def test_d_mixed_files_and_directories() -> None:
    """Files and directories in the same config, each matched by their section."""
    _run_golden_test("test_d")


def test_e_partial_chmod_empty_fields() -> None:
    """Empty user or group fields in the chmod string are skipped."""
    _run_golden_test("test_e")


def test_f_path_vs_name_matching() -> None:
    """Pattern containing / matches rel_path; pattern without / matches name only."""
    _run_golden_test("test_f")


def test_g_single_char_and_char_class_patterns() -> None:
    """? matches exactly one character; [seq] matches a character in the set."""
    _run_golden_test("test_g")


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
    assert expected.read_text() == "root : root : rwx------ ./\n"


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
    assert expected.read_text() == "first : first : rw------- main.py\n"


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
