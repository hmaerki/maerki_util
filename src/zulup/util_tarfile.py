from __future__ import annotations

import hashlib
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zulup.util_json_metafile import MetafileSnapshot


def calculate_tar_checksum(filename_tar: pathlib.Path) -> str:
    with filename_tar.open("rb") as f:
        file_hash = hashlib.file_digest(f, "sha256").hexdigest()
    return f"sha256:{file_hash}"


def verify_tarfile(
    directory: pathlib.Path, metafile_snapshot: MetafileSnapshot
) -> None:
    if metafile_snapshot.tar_checksum is None:
        return
    filename_tar = directory / metafile_snapshot.tarfile_name
    if not filename_tar.is_file():
        raise FileNotFoundError(f"Tarfile not found: '{filename_tar}'")
    actual_checksum = calculate_tar_checksum(filename_tar)
    if actual_checksum != metafile_snapshot.tar_checksum:
        raise ValueError(
            f"Checksum mismatch for '{filename_tar}': "
            f"expected {metafile_snapshot.tar_checksum}, got {actual_checksum}"
        )
