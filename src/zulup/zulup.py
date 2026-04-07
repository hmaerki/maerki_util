from __future__ import annotations

import logging
import pathlib
import subprocess
import sys
import typing

import typer

from . import util_constants, util_systemd_inhibit, util_zulup
from .util_backup_directory import BackupDirectory
from .util_json_metafile import Metafile, MetafileSnapshot
from .util_json_zulup import ZulupJson

logger = logging.getLogger(__file__)


app = typer.Typer()


def _load_backup_directory_from_zulup_backup_json(
    directory: pathlib.Path,
) -> BackupDirectory:
    filename = directory / util_constants.ZULUP_BACKUP_JSON
    zulup_json = ZulupJson.from_file(filename)
    return BackupDirectory(
        directory=pathlib.Path(zulup_json.backup.directory_target),
        backup_name=zulup_json.backup.backup_name,
    )


def _tar_flag() -> str:
    return "-z" if sys.platform == "win32" else "--zstd"


def _tar_list(filename_tar: pathlib.Path) -> set[str]:
    args = ["tar", _tar_flag(), "-tf", str(filename_tar)]
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return set(line.strip() for line in result.stdout.splitlines() if line.strip())


def _tar_extract(filename_tar: pathlib.Path, members: list[str]) -> None:
    if not members:
        return
    args = ["tar", _tar_flag(), "-xf", str(filename_tar), *members]
    subprocess.run(args, check=True)


def _snapshot_by_datetime(metafile: Metafile) -> dict[str, MetafileSnapshot]:
    snapshots = [metafile.current, *metafile.history]
    return {snapshot.snapshot_datetime: snapshot for snapshot in snapshots}


@app.command()
def backup(
    directories: typing.Annotated[
        list[pathlib.Path] | None,
        typer.Argument(
            help="One or more directories to start finding `zulup_backup.json` / `zulup_scan.json`."
        ),
    ] = None,
    full: typing.Annotated[
        bool,
        typer.Option(help="Force a full backup"),
    ] = False,
) -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    with util_systemd_inhibit.systemd_inhibit():
        if directories is None:
            directories = [pathlib.Path.cwd().resolve().absolute()]
        else:
            directories = [d.resolve().absolute() for d in directories]

        zulup = util_zulup.Zulup()
        zulup.log_duration("zulup")
        list_traverse_backup = zulup.traverse_directories(directories=directories)
        zulup.log_duration(
            f"traversed {len(list_traverse_backup)} {util_constants.ZULUP_BACKUP_JSON}"
        )
        list_traverse_backup.verify_history()
        zulup.log_duration("verify_history")
        list_traverse_backup.do_backup(full=full)
        zulup.log_duration("backup")
        zulup.log_duration(
            f"traversed {len(list_traverse_backup)} {util_constants.ZULUP_BACKUP_JSON}"
        )
        zulup.log_duration("done")


@app.command()
def snapshots(
    directory: typing.Annotated[
        pathlib.Path,
        typer.Argument(help="Directory containing zulup_backup.json."),
    ],
) -> None:
    backup_directory = _load_backup_directory_from_zulup_backup_json(
        directory.resolve()
    )
    for snapshot in backup_directory.snapshots:
        typer.echo(str(snapshot.filename_metafile.resolve()))


@app.command(name="list")
def list_snapshot_files(
    filename_metafile: typing.Annotated[
        pathlib.Path,
        typer.Argument(help="Absolute path to snapshot metafile JSON."),
    ],
) -> None:
    metafile = Metafile.from_file(filename_metafile.resolve())
    for entry in metafile.files:
        if entry.verb != "removed":
            typer.echo(entry.path)


@app.command()
def restore(
    filename_metafile: typing.Annotated[
        pathlib.Path,
        typer.Argument(help="Absolute path to snapshot metafile JSON."),
    ],
    files: typing.Annotated[
        list[str] | None,
        typer.Argument(help="Files to restore. If omitted, all files are restored."),
    ] = None,
) -> None:
    filename_metafile = filename_metafile.resolve()
    snapshot_directory = filename_metafile.parent
    metafile = Metafile.from_file(filename_metafile)
    snapshot_map = _snapshot_by_datetime(metafile)

    wanted = set(files) if files else None
    entries = [entry for entry in metafile.files if entry.verb != "removed"]
    if wanted is not None:
        entries = [entry for entry in entries if entry.path in wanted]
        missing = sorted(wanted - {entry.path for entry in entries})
        if missing:
            raise ValueError(f"Files not found in snapshot: {missing}")

    grouped_members: dict[pathlib.Path, list[str]] = {}
    for entry in entries:
        snapshot = snapshot_map.get(entry.snapshot_datetime)
        if snapshot is None:
            raise ValueError(
                f"No snapshot found for datetime {entry.snapshot_datetime}"
            )
        filename_tar = snapshot_directory / snapshot.tarfile_name
        grouped_members.setdefault(filename_tar, []).append(entry.path)

    for filename_tar, rel_paths in grouped_members.items():
        members = _tar_list(filename_tar)
        parent_name = pathlib.Path(metafile.backup.parent).name
        members_to_extract: list[str] = []

        for rel_path in rel_paths:
            candidates = [
                rel_path,
                f"{parent_name}/{rel_path}",
                f"{metafile.backup.backup_name}/{rel_path}",
            ]
            selected = next(
                (candidate for candidate in candidates if candidate in members), None
            )
            if selected is None:
                raise FileNotFoundError(
                    f"'{rel_path}' not found in tarfile '{filename_tar}'"
                )
            members_to_extract.append(selected)

        _tar_extract(filename_tar, members_to_extract)


if __name__ == "__main__":
    app()
