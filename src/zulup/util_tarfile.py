from __future__ import annotations

import logging
import pathlib
import subprocess
import sys

logger = logging.getLogger(__name__)


class TarExtract:
    def __init__(self, filename_tar: pathlib.Path) -> None:
        self.filename_tar = filename_tar

    def list_tarfiles(self) -> set[str]:
        args = [
            "tar",
            "-z" if sys.platform == "win32" else "--zstd",
            "-tf",
            str(self.filename_tar),
        ]
        logger.debug(f"Calling: {' '.join(args)}")
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def restore(self, tarfiles: list[str]) -> None:
        if not tarfiles:
            return
        args = [
            "tar",
            "-z" if sys.platform == "win32" else "--zstd",
            "-xf",
            str(self.filename_tar),
            "--files-from",
            "-",
        ]
        logger.debug(f"Calling: {' '.join(args)} (tarfiles={len(tarfiles)} via stdin)")
        tarfiles_text = "".join(f"{tarfile}\n" for tarfile in tarfiles)
        subprocess.run(
            args,
            input=tarfiles_text,
            text=True,
            check=True,
        )
