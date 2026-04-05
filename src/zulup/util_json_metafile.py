from __future__ import annotations

import dataclasses
import datetime
import enum
import json
import pathlib

from zulup.util_constants import METAFILE_SUFFIX, TARFILE_SUFFIX
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
        assert isinstance(self.path, str)
        assert isinstance(self.size, int)
        assert isinstance(self.modified, str)
        assert isinstance(self.verb, str)
        assert isinstance(self.snapshot_datetime, str)
        check_enum(EnumVerb, self.verb)


@dataclasses.dataclass(frozen=True)
class CurrentFileEntry:
    path: str
    size: int
    modified: str

    def __post_init__(self) -> None:
        assert isinstance(self.path, str)
        assert isinstance(self.size, int)
        assert isinstance(self.modified, str)

    @staticmethod
    def from_file(filepath: pathlib.Path, root: pathlib.Path) -> CurrentFileEntry:
        try:
            stat = filepath.stat()
        except FileNotFoundError:
            raise
        return CurrentFileEntry(
            path=str(filepath.relative_to(root)),
            size=stat.st_size,
            modified=_format_modified(stat.st_mtime),
        )


class CurrentFileEntries(list[CurrentFileEntry]):
    def merge_files(
        self,
        last_files: list[MetafileFileEntry],
        snapshot_datetime: str,
    ) -> list[MetafileFileEntry]:
        last_by_path: dict[str, MetafileFileEntry] = {f.path: f for f in last_files}
        current_by_path: dict[str, CurrentFileEntry] = {f.path: f for f in self}

        result: list[MetafileFileEntry] = []

        for current in self:
            last = last_by_path.get(current.path)
            if last is None:
                verb = EnumVerb.ADDED
            elif last.size == current.size and last.modified == current.modified:
                verb = EnumVerb.UNTOUCHED
            else:
                verb = EnumVerb.MODIFIED
            result.append(
                MetafileFileEntry(
                    path=current.path,
                    size=current.size,
                    modified=current.modified,
                    verb=verb,
                    snapshot_datetime=snapshot_datetime,
                )
            )

        for last in last_files:
            if last.path not in current_by_path:
                result.append(
                    MetafileFileEntry(
                        path=last.path,
                        size=last.size,
                        modified=last.modified,
                        verb=EnumVerb.REMOVED,
                        snapshot_datetime=snapshot_datetime,
                    )
                )

        result.sort(key=lambda e: e.path)
        return result


@dataclasses.dataclass(frozen=True)
class MetafileBackup:
    backup_name: str
    parent: str
    hostname: str
    tar_checksum: str

    def __post_init__(self) -> None:
        assert isinstance(self.backup_name, str)
        assert isinstance(self.parent, str)
        assert isinstance(self.hostname, str)
        assert isinstance(self.tar_checksum, str)


@dataclasses.dataclass(frozen=True)
class MetafileSnapshot:
    snapshot_datetime: str
    snapshot_type: str
    snapshot_stem: str
    tar_checksum: str | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.snapshot_datetime, str)
        assert isinstance(self.snapshot_type, str)
        assert isinstance(self.snapshot_stem, str)
        assert isinstance(self.tar_checksum, (str, type(None)))

    @property
    def tarfile_name(self) -> str:
        return self.snapshot_stem + TARFILE_SUFFIX

    @property
    def metafile_name(self) -> str:
        return self.snapshot_stem + METAFILE_SUFFIX


@dataclasses.dataclass(frozen=True)
class Metafile:
    backup: MetafileBackup
    current: MetafileSnapshot
    history: list[MetafileSnapshot]
    files: list[MetafileFileEntry]

    def __post_init__(self) -> None:
        assert isinstance(self.backup, MetafileBackup)
        assert isinstance(self.current, MetafileSnapshot)
        assert isinstance(self.history, list)
        assert isinstance(self.files, list)

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


def _format_modified(mtime: float) -> str:
    dt = datetime.datetime.fromtimestamp(mtime)
    return dt.strftime("%Y-%m-%d_%H-%M-%S.") + f"{dt.microsecond // 1000:03d}"
