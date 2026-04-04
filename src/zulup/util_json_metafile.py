from __future__ import annotations

import dataclasses
import enum
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


@dataclasses.dataclass(frozen=True)
class MetafileSnapshot:
    snapshot_datetime: str
    snapshot_type: str
    snapshot_stem: str
    tar_checksum: str | None = None


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
