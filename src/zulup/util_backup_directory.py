from __future__ import annotations

import dataclasses
import pathlib

from zulup.util_constants import METAFILE_SUFFIX, TARFILE_SUFFIX
from zulup.util_json_metafile import Metafile


@dataclasses.dataclass(frozen=True)
class SnapshotEntry:
    backup_directory: BackupDirectory
    filename_metafile: pathlib.Path

    @property
    def snapshot_stem(self) -> str:
        return self.filename_metafile.stem

    @property
    def filename_tarfile(self) -> pathlib.Path:
        return self.filename_metafile.with_suffix(TARFILE_SUFFIX)

    @property
    def metafile(self) -> Metafile:
        return Metafile.from_file(self.filename_metafile)


class BackupDirectory:
    def __init__(self, directory: pathlib.Path, backup_name: str) -> None:
        self.directory = directory
        self.backup_name = backup_name
        self._prefix = f"{backup_name}_"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.snapshots = self._scan()

    def _scan(self) -> list[SnapshotEntry]:
        snapshots: list[SnapshotEntry] = []

        for filename_metafile in self.directory.iterdir():
            if not filename_metafile.is_file():
                continue
            if not filename_metafile.name.startswith(self._prefix):
                continue
            if filename_metafile.suffix == METAFILE_SUFFIX:
                snapshots.append(
                    SnapshotEntry(
                        backup_directory=self, filename_metafile=filename_metafile
                    )
                )

        snapshots.sort(key=lambda e: e.snapshot_stem)
        return snapshots

    @property
    def last_snapshot(self) -> SnapshotEntry | None:
        if not self.snapshots:
            return None
        return self.snapshots[-1]

    def verify_history(self, metafile: Metafile) -> None:
        missing: list[str] = []
        for metafile_snapshot in metafile.history:
            metafile_path = self.directory / metafile_snapshot.metafile_name
            if not metafile_path.is_file():
                missing.append(str(metafile_path))
        if missing:
            raise ValueError(
                f"Missing metafile(s) referenced in history of "
                f"'{metafile.current.snapshot_stem}': {missing}"
            )
        for metafile_snapshot in metafile.history:
            metafile_snapshot.verify_tarfile(directory=self.directory)
