from __future__ import annotations

import dataclasses
import json
import pathlib


@dataclasses.dataclass(frozen=True)
class MetafileFileEntry:
    path: str
    size: int
    modified: str
    verb: str
    snapshot_datetime: str


@dataclasses.dataclass(frozen=True)
class MetafileBackup:
    backup_name: str
    parent: str
    hostname: str
    tar_checksum: str


@dataclasses.dataclass(frozen=True)
class MetafileSnapshot:
    snapshot_datetime: str
    snapshot_type: str
    snapshot_stem: str
    tar_checksum: str | None = None


# TODO: Morge with MetafileSnapshot
@dataclasses.dataclass(frozen=True)
class MetafileCurrent:
    snapshot_datetime: str
    snapshot_type: str
    snapshot_stem: str


@dataclasses.dataclass(frozen=True)
class Metafile:
    backup: MetafileBackup
    current: MetafileCurrent
    history: list[MetafileSnapshot]
    files: list[MetafileFileEntry]

    @staticmethod
    def from_file(filename: pathlib.Path) -> Metafile:
        data = json.loads(filename.read_text())
        backup = MetafileBackup(**data["backup"])
        current = MetafileCurrent(**data["current"])
        history = [MetafileSnapshot(**entry) for entry in data["history"]]
        files = [MetafileFileEntry(**entry) for entry in data["files"]]
        return Metafile(
            backup=backup,
            current=current,
            history=history,
            files=files,
        )

    def to_file(self, filename: pathlib.Path) -> None:
        data = {
            "backup": dataclasses.asdict(self.backup),
            "current": dataclasses.asdict(self.current),
            "history": [dataclasses.asdict(entry) for entry in self.history],
            "files": [dataclasses.asdict(entry) for entry in self.files],
        }
        filename.write_text(json.dumps(data, indent=4, sort_keys=True) + "\n")
