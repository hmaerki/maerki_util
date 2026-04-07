from __future__ import annotations

import logging
import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zulup.util_json_metafile import MetafileSnapshot

logger = logging.getLogger(__name__)


class TarExtract:
    def __init__(self, filename_tar: pathlib.Path) -> None:
        self.filename_tar = filename_tar

    @staticmethod
    def _tar_flag() -> str:
        return "-z" if sys.platform == "win32" else "--zstd"

    def list(self) -> set[str]:
        args = ["tar", self._tar_flag(), "-tf", str(self.filename_tar)]
        logger.debug(f"Calling: {' '.join(args)}")
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return set(line.strip() for line in result.stdout.splitlines() if line.strip())

    def restore(self, members: list[str]) -> None:
        if not members:
            return
        args = ["tar", self._tar_flag(), "-xf", str(self.filename_tar), *members]
        logger.debug(f"Calling: {' '.join(args)}")
        subprocess.run(args, check=True)


def verify_tarfile(
    directory: pathlib.Path, metafile_snapshot: MetafileSnapshot
) -> None:
    if metafile_snapshot.tarfile_size is None:
        return
    filename_tar = directory / metafile_snapshot.tarfile_name
    if not filename_tar.is_file():
        raise FileNotFoundError(f"Tarfile not found: '{filename_tar}'")
    actual_size = filename_tar.stat().st_size
    if actual_size != metafile_snapshot.tarfile_size:
        raise ValueError(
            f"Size mismatch for '{filename_tar}': "
            f"expected {metafile_snapshot.tarfile_size}, got {actual_size}"
        )
