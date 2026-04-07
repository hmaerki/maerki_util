from __future__ import annotations

import json
import pathlib

import pytest

from zulup.util_json_zulup import BackupJson, ScanJson

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
def test_backup_json_round_trip(testfile: pathlib.Path) -> None:
    backup_json = BackupJson.from_file(testfile)
    output_file = DIRECTORY_TESTDATA_OUT / testfile.name
    backup_json.to_file(output_file)

    expected = json.loads(testfile.read_text())
    actual = json.loads(output_file.read_text())
    assert actual == expected


@pytest.mark.parametrize(
    "testfile",
    _get_testdata_files("scan_"),
    ids=[f.name for f in _get_testdata_files("scan_")],
)
def test_scan_json_round_trip(testfile: pathlib.Path) -> None:
    scan_json = ScanJson.from_file(testfile)
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
    BackupJson(
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
        BackupJson(
            backup_name=name,
            directory_target="/mnt/backup",
            directory_src=".",
            directory_name_include=True,
        )


def test_backup_defaults_fill_missing_keys(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    filename_defaults = tmp_path / "zulup_backup_defaults.json"
    filename_defaults.write_text(
        json.dumps(
            {
                "directory_target": "/mnt/default_target",
                "directory_src": ".",
                "directory_name_include": False,
                "ignore": [".git/"],
            },
            indent=4,
        )
        + "\n"
    )

    filename_backup = tmp_path / "zulup_backup.json"
    filename_backup.write_text(json.dumps({"backup_name": "project_xy"}, indent=4) + "\n")

    backup_json = BackupJson.from_file(filename_backup)
    assert backup_json.backup_name == "project_xy"
    assert backup_json.directory_target == "/mnt/default_target"
    assert backup_json.directory_src == "."
    assert backup_json.directory_name_include is False
    assert backup_json.ignore == [".git/"]


def test_backup_defaults_local_values_override_defaults(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    filename_defaults = tmp_path / "zulup_backup_defaults.json"
    filename_defaults.write_text(
        json.dumps(
            {
                "directory_target": "/mnt/default_target",
                "directory_src": ".",
                "directory_name_include": False,
                "ignore": [".git/"],
            },
            indent=4,
        )
        + "\n"
    )

    filename_backup = tmp_path / "zulup_backup.json"
    filename_backup.write_text(
        json.dumps(
            {
                "backup_name": "project_xy",
                "directory_target": "/mnt/local_target",
                "directory_name_include": True,
            },
            indent=4,
        )
        + "\n"
    )

    backup_json = BackupJson.from_file(filename_backup)
    assert backup_json.backup_name == "project_xy"
    assert backup_json.directory_target == "/mnt/local_target"
    assert backup_json.directory_src == "."
    assert backup_json.directory_name_include is True
    assert backup_json.ignore == [".git/"]
