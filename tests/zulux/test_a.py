from __future__ import annotations

import pathlib
import subprocess

from zulux.util_zulux import ZuluxTest

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

FILENAME_CHMOD_JSON = DIRECTORY_OF_THIS_FILE / "test_a_zulux_chmod.json"
FILENAME_INPUT = DIRECTORY_OF_THIS_FILE / "test_a_input.txt"
FILENAME_EXPECTED = DIRECTORY_OF_THIS_FILE / "test_a_expected.txt"


def test_a() -> None:
    zt = ZuluxTest(
        filename_zulux_chmod_json=FILENAME_CHMOD_JSON,
        filename_expected=FILENAME_EXPECTED,
    )
    for line in FILENAME_INPUT.read_text().splitlines():
        line = line.strip()
        if line:
            zt.apply_file(pathlib.Path(line))
    zt.write_expected()

    result = subprocess.run(
        ["git", "diff", "--quiet", str(FILENAME_EXPECTED)],
        cwd=DIRECTORY_OF_THIS_FILE,
    )
    assert result.returncode == 0, (
        f"{FILENAME_EXPECTED.name} differs from committed version — "
        "run the test with UPDATE_EXPECTED=1 or commit the new file."
    )
