from __future__ import annotations

import dataclasses
import pathlib

from zulup.util_json_metafile import Metafile

TARFILE_SUFFIX = ".tgz"
METAFILE_SUFFIX = ".json"


@dataclasses.dataclass(frozen=True)
class SnapshotEntry:
    filename_metafile: pathlib.Path

    @property
    def snapshot_stem(self) -> str:
        return self.filename_metafile.stem

    @property
    def filename_tarfile(self) -> pathlib.Path:
        return self.filename_metafile.with_suffix(TARFILE_SUFFIX)


class BackupDirectory:
    def __init__(self, directory: pathlib.Path, backup_name: str) -> None:
        self.directory = directory
        self.backup_name = backup_name
        self._prefix = f"{backup_name}_"
        self.snapshots = self._scan()

    def _scan(self) -> list[SnapshotEntry]:
        snapshots: list[SnapshotEntry] = []

        for filename_metafile in self.directory.iterdir():
            if not filename_metafile.is_file():
                continue
            if not filename_metafile.name.startswith(self._prefix):
                continue
            if filename_metafile.suffix == METAFILE_SUFFIX:
                snapshots.append(SnapshotEntry(filename_metafile=filename_metafile))

        snapshots.sort(key=lambda e: e.snapshot_stem)
        return snapshots

    @property
    def last_snapshot(self) -> SnapshotEntry | None:
        if not self.snapshots:
            return None
        return self.snapshots[-1]

    @property
    def last_metafile(self) -> Metafile | None:
        if self.last_snapshot is None:
            return None
        return Metafile.from_file(self.last_snapshot.filename_metafile)
