from __future__ import annotations

import logging
import os
import pathlib
import sys
import typing

import typer

from . import util_constants
from .util_zulux import ZuluxReal, ZuluxTest

logger = logging.getLogger(__file__)


app = typer.Typer(
    help=f"Zulux set permissions tool. Documentation: {util_constants.README_URL}",
)


def _find_chmod_json_files(
    directory: pathlib.Path,
) -> list[tuple[pathlib.Path, pathlib.Path]]:
    """
    Recursively walk directory, stopping descent into any subdirectory that
    contains a *zulux_chmod.json.  Returns a list of (json_file, root_dir)
    tuples where root_dir is the directory the json file governs.
    """
    results: list[tuple[pathlib.Path, pathlib.Path]] = []

    for dirpath, dirnames, filenames in os.walk(directory):
        current = pathlib.Path(dirpath)
        json_files = sorted(
            current / f
            for f in filenames
            if f.endswith(util_constants.ZULUX_CHMOD_JSON_SUFFIX)
        )
        if json_files:
            for json_file in json_files:
                # A plain 'zulux_chmod.json' governs current itself.
                # A prefixed 'http_zulux_chmod.json' governs the sibling 'http/' directory.
                prefix = json_file.name[: -len(util_constants.ZULUX_CHMOD_JSON_SUFFIX)]
                if prefix:
                    prefix = prefix.rstrip("_")
                    sibling = current / prefix
                    if not sibling.is_dir():
                        logger.error(
                            "Sibling directory '%s' required by '%s' does not exist — skipping.",
                            sibling,
                            json_file.name,
                        )
                        continue
                    results.append((json_file, sibling))
                else:
                    results.append((json_file, current))
            # Do not recurse deeper once a config file is found at this level.
            dirnames.clear()
        else:
            dirnames.sort()

    return results


def _apply_json(
    json_file: pathlib.Path, directory_root: pathlib.Path, dry_run: bool
) -> None:
    if dry_run:
        print(json_file)
        zulux: ZuluxReal | ZuluxTest = ZuluxTest(
            zulux_json=json_file,
            f_expected=sys.stdout,
        )
    else:
        logger.info("Applying %s to %s", json_file.name, directory_root)
        zulux = ZuluxReal(zulux_json=json_file, directory_root=directory_root)

    zulux.apply_directory_self()

    for dirpath, dirnames, filenames in os.walk(directory_root):
        dirnames.sort()
        current = pathlib.Path(dirpath)
        rel_dir = current.relative_to(directory_root)
        if rel_dir != pathlib.Path("."):
            zulux.apply_directory(rel_dir)
        for filename in sorted(filenames):
            zulux.apply_file(rel_dir / filename)


@app.callback()
def main(
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


@app.command()
def apply(
    directories: typing.Annotated[
        list[pathlib.Path],
        typer.Argument(help="One or more directories to process."),
    ],
    dry_run: typing.Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Discover config files and log what would be done, without changing permissions.",
        ),
    ] = False,
) -> None:
    """Traverse directories, find *zulux_chmod.json files, and apply permissions."""
    for directory in directories:
        if not directory.is_dir():
            logger.error("Not a directory: %s", directory)
            raise typer.Exit(code=1)
        found = _find_chmod_json_files(directory)
        if not found:
            logger.warning(
                "No *%s found under %s",
                util_constants.ZULUX_CHMOD_JSON_SUFFIX,
                directory,
            )
            continue
        for json_file, root in found:
            _apply_json(json_file, root, dry_run=dry_run)


if __name__ == "__main__":
    app()
