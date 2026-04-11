from __future__ import annotations

import logging
import pathlib
import typing

import typer

logger = logging.getLogger(__file__)


app = typer.Typer()


@app.command()
def create(
    filename_xml: typing.Annotated[
        pathlib.Path,
        typer.Argument(help="XML file"),
    ],
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


if __name__ == "__main__":
    app()
