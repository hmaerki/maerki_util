from __future__ import annotations

import json
import pathlib

import pytest

from zulup.util_json_zulup import ZulupBackup, ZulupJson, ZulupScanJson

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA = DIRECTORY_OF_THIS_FILE / "testdata_zulup"
DIRECTORY_TESTDATA_OUT = DIRECTORY_OF_THIS_FILE / "testdata_zulup_out"


@pytest.fixture(autouse=True)
def _setup_output_dir() -> None:
    DIRECTORY_TESTDATA_OUT.mkdir(exist_ok=True)


def _get_testdata_files(prefix: str) -> list[pathlib.Path]:
    return sorted(DIRECTORY_TESTDATA.glob(f"{prefix}*.json"))


@pytest.mark.parametrize(
    "testfile",
    _get_testdata_files("backup_"),
    ids=[f.name for f in _get_testdata_files("backup_")],
)
def test_zulup_backup_json_round_trip(testfile: pathlib.Path) -> None:
    zulup_json = ZulupJson.from_file(testfile)
    output_file = DIRECTORY_TESTDATA_OUT / testfile.name
    zulup_json.to_file(output_file)

    expected = json.loads(testfile.read_text())
    actual = json.loads(output_file.read_text())
    assert actual == expected


@pytest.mark.parametrize(
    "testfile",
    _get_testdata_files("scan_"),
    ids=[f.name for f in _get_testdata_files("scan_")],
)
def test_zulup_scan_json_round_trip(testfile: pathlib.Path) -> None:
    scan_json = ZulupScanJson.from_file(testfile)
    output_file = DIRECTORY_TESTDATA_OUT / testfile.name
    scan_json.to_file(output_file)

    expected = json.loads(testfile.read_text())
    actual = json.loads(output_file.read_text())
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    ["valid_name", "project123", "A_B_C"],
)
def test_backup_name_valid(name: str) -> None:
    ZulupBackup(
        backup_name=name,
        directory_target="/mnt/backup",
        directory_src=".",
        directory_name_include=True,
    )


@pytest.mark.parametrize(
    "name",
    ["has space", "with-dash", "dot.name", "slash/bad", ""],
)
def test_backup_name_invalid(name: str) -> None:
    with pytest.raises(ValueError, match="backup_name"):
        ZulupBackup(
            backup_name=name,
            directory_target="/mnt/backup",
            directory_src=".",
            directory_name_include=True,
        )
