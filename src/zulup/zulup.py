from __future__ import annotations

import logging
import pathlib
import typing

import typer

from . import util_constants, util_systemd_inhibit, util_zulup

logger = logging.getLogger(__file__)


app = typer.Typer()


@app.command()
def backup(
    directories: typing.Annotated[
        list[pathlib.Path] | None,
        typer.Argument(help="One or more directories to start finding `zulup.json`."),
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
            f"traversed {len(list_traverse_backup)} {util_constants.ZULUP_JSON}"
        )
        list_traverse_backup.verify_history()
        zulup.log_duration("verify_history")
        list_traverse_backup.do_backup(full=full)
        zulup.log_duration("backup")
        zulup.log_duration(
            f"traversed {len(list_traverse_backup)} {util_constants.ZULUP_JSON}"
        )
        zulup.log_duration("done")


if __name__ == "__main__":
    app()
