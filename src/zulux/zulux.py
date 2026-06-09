from __future__ import annotations

import logging
import typing

import typer

from . import util_constants

logger = logging.getLogger(__file__)


app = typer.Typer(
    invoke_without_command=True,
    rich_markup_mode="markdown",
    help=f"Zulux set permissions tool. Documentation: {util_constants.README_URL}",
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


if __name__ == "__main__":
    app()
