from __future__ import annotations

import logging
import pathlib
import typing

import typer

from . import util_constants, util_systemd_inhibit, util_zulup
from .util_json_metafile import Metafile
from .util_json_zulup import BackupJson
from .util_tarfile import TarExtract

logger = logging.getLogger(__file__)


app = typer.Typer(
    invoke_without_command=True,
    rich_markup_mode="markdown",
    help=f"Zulup backup tool. Documentation: {util_constants.README_URL}",
)


@app.callback()
def main(
    ctx: typer.Context,
    debug: typing.Annotated[
        bool,
        typer.Option("--debug", help="Set log level to DEBUG (default: INFO)"),
    ] = False,
) -> None:
    console_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(message)s",
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.setLevel(console_level)
    if ctx.invoked_subcommand is None:
        ctx.invoke(backup)


@app.command()
def backup(
    directories: typing.Annotated[
        list[pathlib.Path] | None,
        typer.Argument(
            help=(
                "One or more directories to start finding "
                f"`{util_constants.ZULUP_BACKUP_JSON}` / "
                f"`{util_constants.ZULUP_SCAN_JSON}`."
            )
        ),
    ] = None,
    full: typing.Annotated[
        bool,
        typer.Option(help="Force a full backup"),
    ] = False,
) -> None:
    with util_systemd_inhibit.systemd_inhibit():
        if directories is None:
            directories = [pathlib.Path.cwd().resolve().absolute()]
        else:
            directories = [d.resolve().absolute() for d in directories]

        zulup = util_zulup.Zulup()
        zulup.log_duration("zulup")
        traverse = zulup.traverse_directories(directories=directories)
        zulup.log_duration(
            f"Found {len(traverse.list_dir_zulup_json)} {util_constants.ZULUP_BACKUP_JSON}"
        )
        for dir_zulup_json in traverse.list_dir_zulup_json:
            dir_zulup_json.verify_history()
            zulup.log_duration("verify_history")
            args = dir_zulup_json.backup_arguments(
                full=full,
                snapshot_datetime=None,
            )
            dir_zulup_json.do_backup(args=args)
            zulup.log_duration("backup")

        zulup.log_duration("done")


@app.command()
def snapshots(
    directory: typing.Annotated[
        pathlib.Path,
        typer.Argument(
            help=f"Directory containing {util_constants.ZULUP_BACKUP_JSON}."
        ),
    ],
) -> None:
    filename = directory.resolve() / util_constants.ZULUP_BACKUP_JSON
    backup_json = BackupJson.from_file(filename)
    backup_directory = backup_json.backup_directory
    for snapshot in backup_directory.snapshots:
        typer.echo(str(snapshot.filename_metafile.resolve()))


@app.command(name="list")
def list_snapshot_files(
    filename_metafile: typing.Annotated[
        pathlib.Path,
        typer.Argument(
            help="Absolute path to snapshot ('project_xxx_2026-05-22_xxx.json')."
        ),
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
        typer.Argument(
            help="Absolute path to snapshot ('project_xxx_2026-05-22_xxx.json')."
        ),
    ],
    files: typing.Annotated[
        list[str] | None,
        typer.Argument(help="Files to restore. If omitted, all files are restored."),
    ] = None,
) -> None:
    filename_metafile = filename_metafile.resolve()
    snapshot_directory = filename_metafile.parent
    metafile = Metafile.from_file(filename_metafile)
    snapshot_map = metafile.by_datetime

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
        tar_extract = TarExtract(filename_tar)
        members = tar_extract.list()
        parent_name = pathlib.Path(metafile.backup.parent).name
        members_to_restore: list[str] = []

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
            members_to_restore.append(selected)

        tar_extract.restore(members_to_restore)


if __name__ == "__main__":
    app()
