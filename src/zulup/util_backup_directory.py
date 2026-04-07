from __future__ import annotations

import dataclasses
import pathlib
import typing

from zulup.util_constants import METAFILE_SUFFIX, TARFILE_SUFFIX
from zulup.util_json_metafile import Metafile
from zulup.util_tarfile import verify_tarfile

if typing.TYPE_CHECKING:
    from zulup.util_json_metafile import MetafileFileEntry, MetafileSnapshot
    from zulup.util_traverse_zulup import BackupArguments


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
            verify_tarfile(
                directory=self.directory, metafile_snapshot=metafile_snapshot
            )

    def backup_arguments(
        self, full: bool, snapshot_datetime: str | None, directory_target: pathlib.Path
    ) -> BackupArguments:
        """Build BackupRunContext from backup state."""
        from zulup import util_constants
        from zulup.util_traverse_zulup import BackupArguments

        # Get last metafile's file entries (empty if no previous backup or full backup)
        last_files: list[MetafileFileEntry] = []
        last_snapshot: SnapshotEntry | None = None
        history: list[MetafileSnapshot] = []

        if not full and self.last_snapshot is not None:
            last_snapshot = self.last_snapshot
            last_files = last_snapshot.metafile.files
            prev_metafile = last_snapshot.metafile
            history = [prev_metafile.current] + prev_metafile.history

        snapshot_datetime = snapshot_datetime or util_constants.now_text()
        is_incr = last_snapshot is not None
        snapshot_type = "incr" if is_incr else "full"
        filename_tar = (
            directory_target
            / f"{self.backup_name}_{snapshot_datetime}_{snapshot_type}{util_constants.TARFILE_SUFFIX}"
        )
        return BackupArguments(
            last_files=last_files,
            last_snapshot=last_snapshot,
            history=history,
            snapshot_datetime=snapshot_datetime,
            snapshot_type=snapshot_type,
            filename_tar=filename_tar,
        )
