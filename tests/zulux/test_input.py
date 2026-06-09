from __future__ import annotations

import pathlib
import subprocess

import pytest

from zulux.util_zulux import ZuluxTest

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_INPUT_FILES = sorted(DIRECTORY_OF_THIS_FILE.glob("test_*_input.txt"))


@pytest.mark.parametrize(
    "input_file",
    _INPUT_FILES,
    ids=[f.name.removesuffix("_input.txt") for f in _INPUT_FILES],
)
def test_input(input_file: pathlib.Path) -> None:
    """Run the golden-file test for every test_*_input.txt found in this directory."""
    test_name = input_file.name.removesuffix("_input.txt")
    zt = ZuluxTest(
        filename_zulux_chmod_json=DIRECTORY_OF_THIS_FILE
        / f"{test_name}_zulux_chmod.json",
        filename_expected=DIRECTORY_OF_THIS_FILE / f"{test_name}_expected.txt",
    )
    for line in input_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
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
