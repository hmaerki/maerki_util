from __future__ import annotations

import dataclasses
import logging
import pathlib
import subprocess
import tempfile
import time
import typing

import typer

logger = logging.getLogger(__file__)


app = typer.Typer()


class Zulup:
    def __init__(self) -> None:
        self.begin_s = time.monotonic()

    @property
    def duration_s(self) -> float:
        return time.monotonic() - self.begin_s

    def log_duration(self, tag: str) -> None:
        logger.debug(f"{tag}: {self.duration_s:0.3f}s.")

    def backup(self, filename_target: pathlib.Path) -> None:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_filename = pathlib.Path(temp_file.name)
            self.file_data_list.write_ftp(temp_filename)
        try:
            args = [
                "tar",
                # "-I",
                # "--use-compress-program",
                # "zstd -T0",
                "--zstd",
                "--files-from",
                str(temp_filename),
                "-cf",
                str(filename_target),
            ]
            logger.debug(f"Calling: {' '.join(args)}")
            subprocess.run(args, cwd=self.directory_src, check=True)
        finally:
            temp_filename.unlink(missing_ok=True)

        size_bytes = filename_target.stat().st_size
        duration_s = self.duration_s
        self.log_duration("tar created")
        logger.debug(
            f"Created {filename_target} with {size_bytes / 1e6:0.0f}MByte in {duration_s:0.0f}s. {size_bytes / duration_s / 1e6:0.0f}MByte/s"
        )


@app.command()
def backup(
    directory: typing.Annotated[
        pathlib.Path,
        typer.Option(help="The directory to start finding `zulup.json`."),
    ] = pathlib.Path.home(),
    full: typing.Annotated[
        bool,
        typer.Option(help="Force a full backup"),
    ] = False,
) -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    zulup = Zulup()
    zulup.backup(filename_target=pathlib.Path("/home/maerki/tmp_backup.tgz"))


if __name__ == "__main__":
    app()
