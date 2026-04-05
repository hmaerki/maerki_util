from __future__ import annotations

import logging
import pathlib
import typing

import typer

from . import util_constants, util_zulup

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

    if directories is None:
        directories = [pathlib.Path.home()]

    zulup = util_zulup.Zulup()
    list_traverse_backup = zulup.traverse_directories(directories=directories)
    zulup.log_duration(
        f"traversed {len(list_traverse_backup)} {util_constants.ZULUP_JSON}"
    )
    list_traverse_backup.verify_history()
    zulup.log_duration("done")


if __name__ == "__main__":
    app()
