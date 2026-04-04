from __future__ import annotations

import json
import pathlib

import pytest

from zulup.util_json_metafile import Metafile

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata_metafiles"
DIRECTORY_TESTDATA_OUT = DIRECTORY_OF_THIS_FILE / "testdata_metafiles_out"


@pytest.fixture(autouse=True)
def _setup_output_dir() -> None:
    DIRECTORY_TESTDATA_OUT.mkdir(exist_ok=True)


def _get_testdata_files() -> list[pathlib.Path]:
    return sorted(DIRECTORY_TESTDATA.glob("*.json"))


@pytest.mark.parametrize(
    "testfile",
    _get_testdata_files(),
    ids=[f.name for f in _get_testdata_files()],
)
def test_metafile_round_trip(testfile: pathlib.Path) -> None:
    metafile = Metafile.from_file(testfile)
    output_file = DIRECTORY_TESTDATA_OUT / testfile.name
    metafile.to_file(output_file)

    expected = json.loads(testfile.read_text())
    actual = json.loads(output_file.read_text())
    assert actual == expected
