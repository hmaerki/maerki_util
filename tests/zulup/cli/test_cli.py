from __future__ import annotations

import pathlib

from typer.testing import CliRunner

from zulup.util_backup_directory import BackupDirectory
from zulup.util_pytest import TestProjectDirectory
from zulup.zulup import app


def _create_backup_history(project: TestProjectDirectory) -> BackupDirectory:
    project.create_file("a.txt", "a-v1\n")
    project.create_file("b.txt", "b-v1\n")
    project.create_file("c.txt", "c-v1\n")
    project.create_backup_json(directory_name_include=False, ignore=[".git/"])

    project.do_backup(snapshot_datetime="2026-04-07_10-00-00")

    project.create_file("d.txt", "d-v1\n")
    project.create_file("b.txt", "b-v2-modified\n")
    (project.src / "c.txt").unlink()

    project.do_backup(snapshot_datetime="2026-04-07_10-00-01")

    return project.get_backup_directory()


def test_cli_snapshots_lists_snapshot_metafiles(project: TestProjectDirectory) -> None:
    backup_directory = _create_backup_history(project)

    runner = CliRunner()
    result = runner.invoke(app, ["snapshots", str(project.src)])

    assert result.exit_code == 0
    expected = [
        str(snapshot.filename_metafile.resolve())
        for snapshot in backup_directory.snapshots
    ]
    assert result.stdout.splitlines() == expected


def test_cli_list_omits_removed_files(project: TestProjectDirectory) -> None:
    backup_directory = _create_backup_history(project)
    incr_metafile = backup_directory.snapshots[1].filename_metafile

    runner = CliRunner()
    result = runner.invoke(app, ["list", str(incr_metafile)])

    assert result.exit_code == 0
    listed = set(result.stdout.splitlines())
    assert listed == {"a.txt", "b.txt", "d.txt"}


def test_cli_restore_restores_selected_files(project: TestProjectDirectory) -> None:
    backup_directory = _create_backup_history(project)
    incr_metafile = backup_directory.snapshots[1].filename_metafile

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["restore", str(incr_metafile), "a.txt", "b.txt"],
        )

        assert result.exit_code == 0
        cwd = pathlib.Path.cwd()
        assert (cwd / "a.txt").read_text() == "a-v1\n"
        assert (cwd / "b.txt").read_text() == "b-v2-modified\n"
        assert not (cwd / "d.txt").exists()
