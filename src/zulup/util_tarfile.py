from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zulup.util_json_metafile import MetafileSnapshot


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
