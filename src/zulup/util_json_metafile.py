from __future__ import annotations

import dataclasses
import datetime
import enum
import json
import logging
import pathlib
import typing

from zulup.util_constants import METAFILE_SUFFIX, TARFILE_SUFFIX
from zulup.util_json import check_enum

if typing.TYPE_CHECKING:
    from zulup.util_traverse_zulup import BackupArguments

logger = logging.getLogger(__name__)


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
    def merge(self, args: BackupArguments) -> list[MetafileFileEntry]:
        return self.merge_files(
            last_files=args.last_files,
            snapshot_datetime=args.snapshot_datetime,
        )

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
                entry_snapshot_datetime = snapshot_datetime
            elif last.size == current.size and last.modified == current.modified:
                verb = EnumVerb.UNTOUCHED
                entry_snapshot_datetime = last.snapshot_datetime
            else:
                verb = EnumVerb.MODIFIED
                entry_snapshot_datetime = snapshot_datetime
            result.append(
                MetafileFileEntry(
                    path=current.path,
                    size=current.size,
                    modified=current.modified,
                    verb=verb,
                    snapshot_datetime=entry_snapshot_datetime,
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

    def __post_init__(self) -> None:
        assert isinstance(self.backup_name, str)
        assert isinstance(self.parent, str)
        assert isinstance(self.hostname, str)


@dataclasses.dataclass(frozen=True)
class MetafileSnapshot:
    snapshot_datetime: str
    snapshot_type: str
    snapshot_stem: str
    tarfile_size: int | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.snapshot_datetime, str)
        assert isinstance(self.snapshot_type, str)
        assert isinstance(self.snapshot_stem, str)
        assert isinstance(self.tarfile_size, (int, type(None)))

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

    @property
    def by_datetime(self) -> dict[str, MetafileSnapshot]:
        snapshots = [self.current, *self.history]
        return {snapshot.snapshot_datetime: snapshot for snapshot in snapshots}

    @property
    def stat_total_file(self) -> list[MetafileFileEntry]:
        return [f for f in self.files if f.verb != EnumVerb.REMOVED]

    @property
    def stat_backup_file(self) -> list[MetafileFileEntry]:
        return [f for f in self.files if f.verb in (EnumVerb.ADDED, EnumVerb.MODIFIED)]

    @property
    def stat_total_size_byte(self) -> int:
        return sum(f.size for f in self.stat_total_file)

    @property
    def stat_backup_size_byte(self) -> int:
        return sum(f.size for f in self.stat_backup_file)

    def stats(self, duration_s: float) -> None:
        try:
            speed_bytes_s = self.stat_backup_size_byte / duration_s
        except ZeroDivisionError:
            speed_bytes_s = 0.0
        logger.info(
            f"Total: {len(self.stat_total_file)} files, {self.stat_total_size_byte / 1_000_000:.1f} MByte. Backup: {len(self.stat_backup_file)} files, {self.stat_backup_size_byte / 1_000_000:.1f} MByte, {duration_s:.1f}s, {speed_bytes_s / 1_000_000:.1f}MByte/s."
        )

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
