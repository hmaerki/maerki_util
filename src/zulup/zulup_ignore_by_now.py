from __future__ import annotations

import dataclasses
import logging
import pathlib
import subprocess
import tempfile
import time
import typing
from datetime import datetime

import typer

logger = logging.getLogger(__file__)


app = typer.Typer()

FILENAME_ZULUP_FILELIST = "zulup_filelist.txt"


@dataclasses.dataclass(frozen=True)
class FileData:
    relative_name: str
    size_in_bytes: int
    timestamp: str

    @property
    def ftp_order(self) -> tuple[bool, str]:
        is_zulup_filelist = FILENAME_ZULUP_FILELIST != self.relative_name
        return (is_zulup_filelist, self.relative_name)

    @property
    def as_text(self) -> str:
        return f"{self.timestamp} {self.size_in_bytes:8d} {self.relative_name}"

    @classmethod
    def from_file_path(
        cls, directory: pathlib.Path, file_path: pathlib.Path
    ) -> FileData:
        stat = file_path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)
        milliseconds = int((stat.st_mtime - int(stat.st_mtime)) * 1000)
        timestamp = modified.strftime("%Y-%m-%d_%H-%M-%S") + f".{milliseconds:03d}"
        relative_name = file_path.relative_to(directory).as_posix()
        return cls(
            relative_name=relative_name,
            size_in_bytes=stat.st_size,
            timestamp=timestamp,
        )


class Filelist(list[FileData]):
    @classmethod
    def factory(cls, directory: pathlib.Path) -> Filelist:
        files = [file_path for file_path in directory.rglob("*") if file_path.is_file()]
        return cls(
            [FileData.from_file_path(directory, file_path) for file_path in files]
        )

    def write_list(self, filename: pathlib.Path) -> None:
        sorted_entries = sorted(self, key=lambda file_data: file_data.relative_name)
        content = "\n".join(file_data.as_text for file_data in sorted_entries)
        filename.write_text(content)

    def write_ftp(self, filename: pathlib.Path) -> None:
        ftp_sorted = sorted(self, key=lambda file_data: file_data.ftp_order)
        ftp_filelist = "\n".join(file_data.relative_name for file_data in ftp_sorted)
        filename.write_text(ftp_filelist + "\n")


class Zulup:
    def __init__(self, directory_src: pathlib.Path) -> None:
        self.directory_src = directory_src
        self.file_data_list = Filelist.factory(self.directory_src)
        self.begin_s = time.monotonic()

    def create_file_list(self) -> None:
        self.file_data_list.write_list(self.directory_src / FILENAME_ZULUP_FILELIST)

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

        duration_s = time.monotonic() - self.begin_s
        size_bytes = filename_target.stat().st_size
        logger.debug(
            f"Created {filename_target} with {size_bytes / 1e6:0.0f}MByte in {duration_s:0.0f}s. {size_bytes / duration_s / 1e6:0.0f}MByte/s"
        )


@app.command()
def backup(
    directory: typing.Annotated[
        pathlib.Path,
        typer.Option(
            help="Force upload of all files",
        ),
    ] = pathlib.Path("/home/maerki/Downloads"),
) -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    zulup = Zulup(directory_src=directory)
    zulup.create_file_list()
    zulup.backup(filename_target=pathlib.Path("/home/maerki/tmp_backup.tgz"))


if __name__ == "__main__":
    app()
