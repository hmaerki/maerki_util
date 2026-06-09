from __future__ import annotations

import pathlib
import subprocess

import pytest

from zulux.util_zulux import ZuluxTest

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata"

_INPUT_FILES = sorted(DIRECTORY_TESTDATA.glob("test_*_input.txt"))


@pytest.mark.parametrize(
    "input_file",
    _INPUT_FILES,
    ids=[f.name.removesuffix("_input.txt") for f in _INPUT_FILES],
)
def test_input(input_file: pathlib.Path) -> None:
    """Run the golden-file test for every test_*_input.txt found in this directory."""
    test_name = input_file.name.removesuffix("_input.txt")
    filename_expected = DIRECTORY_TESTDATA / f"{test_name}_expected.txt"
    with filename_expected.open("w") as f_expected:
        zt = ZuluxTest(
            zulux_json=DIRECTORY_TESTDATA / f"{test_name}_zulux_chmod.json",
            f_expected=f_expected,
        )
        for line in input_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith("/"):
                zt.apply_directory(pathlib.Path(line.rstrip("/")))
            else:
                zt.apply_file(pathlib.Path(line))

    result = subprocess.run(
        ["git", "diff", "--quiet", f"{test_name}_expected.txt"],
        cwd=DIRECTORY_TESTDATA,
    )
    assert result.returncode == 0, (
        f"{test_name}_expected.txt differs from committed version."
    )
