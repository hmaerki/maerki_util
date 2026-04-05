from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import pathlib

from zulup.util_json import check_enum


class EnumVerb(enum.StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    UNTOUCHED = "untouched"
    REMOVED = "removed"


@dataclasses.dataclass(frozen=True)
class MetafileFileEntry:
    path: str
    size: int
    modified: str
    verb: str
    snapshot_datetime: str

    def __post_init__(self) -> None:
        check_enum(EnumVerb, self.verb)


@dataclasses.dataclass(frozen=True)
class MetafileBackup:
    backup_name: str
    parent: str
    hostname: str
    tar_checksum: str


TARFILE_SUFFIX = ".tgz"


def calculate_tar_checksum(filename_tar: pathlib.Path) -> str:
    with filename_tar.open("rb") as f:
        file_hash = hashlib.file_digest(f, "sha256").hexdigest()
    return f"sha256:{file_hash}"


@dataclasses.dataclass(frozen=True)
class MetafileSnapshot:
    snapshot_datetime: str
    snapshot_type: str
    snapshot_stem: str
    tar_checksum: str | None = None

    def verify_tarfile(self, directory: pathlib.Path) -> None:
        if self.tar_checksum is None:
            return
        filename_tar = directory / (self.snapshot_stem + TARFILE_SUFFIX)
        if not filename_tar.is_file():
            raise FileNotFoundError(f"Tarfile not found: '{filename_tar}'")
        actual_checksum = calculate_tar_checksum(filename_tar)
        if actual_checksum != self.tar_checksum:
            raise ValueError(
                f"Checksum mismatch for '{filename_tar}': "
                f"expected {self.tar_checksum}, got {actual_checksum}"
            )


@dataclasses.dataclass(frozen=True)
class Metafile:
    backup: MetafileBackup
    current: MetafileSnapshot
    history: list[MetafileSnapshot]
    files: list[MetafileFileEntry]

    @staticmethod
    def from_file(filename: pathlib.Path) -> Metafile:
        data = json.loads(filename.read_text())
        backup = MetafileBackup(**data["backup"])
        current = MetafileSnapshot(**data["current"])
        history = [MetafileSnapshot(**entry) for entry in data["history"]]
        files = [MetafileFileEntry(**entry) for entry in data["files"]]
        return Metafile(
            backup=backup,
            current=current,
            history=history,
            files=files,
        )

    @staticmethod
    def _snapshot_dict(snapshot: MetafileSnapshot) -> dict[str, object]:
        return {k: v for k, v in dataclasses.asdict(snapshot).items() if v is not None}

    def to_file(self, filename: pathlib.Path) -> None:
        data = {
            "backup": dataclasses.asdict(self.backup),
            "current": self._snapshot_dict(self.current),
            "history": [self._snapshot_dict(entry) for entry in self.history],
            "files": [dataclasses.asdict(entry) for entry in self.files],
        }
        filename.write_text(json.dumps(data, indent=4, sort_keys=True) + "\n")
