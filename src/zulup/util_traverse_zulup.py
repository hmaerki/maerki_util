from __future__ import annotations

import dataclasses
import fnmatch
import logging
import os
import pathlib
import socket
import subprocess
import sys
import tempfile

from . import util_constants
from .util_backup_directory import BackupDirectory, SnapshotEntry
from .util_constants import ZULUP_BACKUP_JSON, ZULUP_SCAN_JSON
from .util_json_metafile import (
    CurrentFileEntries,
    CurrentFileEntry,
    EnumVerb,
    Metafile,
    MetafileBackup,
    MetafileFileEntry,
    MetafileSnapshot,
)
from .util_json_zulup import BackupJson, ScanJson, ZulupIgnore
from .util_logging import snapshot_logfile

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BackupArguments:
    last_files: list[MetafileFileEntry]
    last_snapshot: SnapshotEntry | None
    history: list[MetafileSnapshot]
    snapshot_datetime: str
    snapshot_type: str
    filename_tar: pathlib.Path

    @property
    def is_incr(self) -> bool:
        return self.last_snapshot is not None

    def create_metafile_snapshot(self, tarfile_size: int) -> MetafileSnapshot:
        """Create MetafileSnapshot from this context and tarfile size."""
        return MetafileSnapshot(
            snapshot_datetime=self.snapshot_datetime,
            snapshot_type=self.snapshot_type,
            snapshot_stem=self.filename_tar.stem,
            tarfile_size=tarfile_size,
        )


@dataclasses.dataclass
class DirectoryBackupJson:
    directory: pathlib.Path
    backup_json: BackupJson

    def __post_init__(self) -> None:
        assert isinstance(self.directory, pathlib.Path)
        assert isinstance(self.backup_json, BackupJson)

    @property
    def zulup_ignore(self) -> ZulupIgnore:
        return ZulupIgnore(self.backup_json.ignore or [])

    @property
    def directory_src(self) -> pathlib.Path:
        return self.directory / self.backup_json.directory_src

    @property
    def directory_target(self) -> pathlib.Path:
        return pathlib.Path(self.backup_json.directory_target)

    @property
    def backup_directory(self) -> BackupDirectory:
        return BackupDirectory(
            directory=self.directory_target,
            backup_name=self.backup_json.backup_name,
        )

    @property
    def files(self) -> list[str]:
        ignore = self.zulup_ignore
        top = str(self.directory_src)
        top_len = len(top) + 1  # +1 for trailing separator
        files: list[str] = []

        for dirpath, dirnames, filenames in os.walk(top):
            rel_prefix = dirpath[top_len:] + "/" if len(dirpath) > top_len - 1 else ""

            # Filter directories in-place (sorted) to control os.walk traversal
            dirnames[:] = [
                d
                for d in sorted(dirnames)
                if ignore.is_included(
                    d, f"{rel_prefix}{d}" if rel_prefix else d, is_dir=True
                )
            ]

            for name in sorted(filenames):
                if name in (
                    util_constants.ZULUP_BACKUP_JSON,
                    util_constants.ZULUP_SCAN_JSON,
                ):
                    continue
                rel_path = f"{rel_prefix}{name}" if rel_prefix else name
                if ignore.is_included(name, rel_path, is_dir=False):
                    files.append(rel_path)

        files.sort()
        return files

    @property
    def current_files(self) -> CurrentFileEntries:
        return CurrentFileEntries(
            [
                CurrentFileEntry.from_file(
                    filepath=self.directory_src / rel_path,
                    root=self.directory_src,
                )
                for rel_path in self.files
            ]
        )

    def verify_history(self) -> None:
        backup_directory = self.backup_directory
        if backup_directory.last_snapshot is not None:
            metafile = backup_directory.last_snapshot.metafile
            backup_directory.verify_history(metafile=metafile)

    def do_backup(self, args: BackupArguments) -> None:
        """
        See AGENTS.md

        * Merge `last_metafile` with `current_filelist` into `new_metafile`. In this step the `verb` will be updated:
            * `added`: If the file is new.
            * `removed`: if the file is gone.
            * `untouched`: If the file size and modification time have not changed.
            * `modified`: else
        * Create a file list as input into `tar --files-from`: All files which are `added` or `modified`.
        * Call `tar --zstd --files-from ... -cf <directory_target>/<snapshot_stem>.tgz_tmp`.
        * Read the file size of `<directory_target>/<snapshot_stem>.tgz_tmp` and store it as `tarfile_size` in `current` of `new_metafile`.
        * Store `new_metafile` in `<directory_target>/<snapshot_stem>.json`.
        * Rename `<snapshot_stem>.tgz_tmp` to `<snapshot_stem>.tgz`
        """

        merged_files = self.current_files.merge(args)

        logger.info(f"snapshot: {args.filename_tar}")
        with snapshot_logfile(
            filename_log=args.filename_tar.with_suffix(util_constants.LOGFILE_SUFFIX)
        ):
            tarfile_size = self.do_tar(
                merged_files=merged_files,
                filename_target=args.filename_tar,
            )

            metafile = Metafile(
                backup=MetafileBackup(
                    backup_name=self.backup_json.backup_name,
                    parent=str(self.directory_src),
                    hostname=socket.gethostname(),
                ),
                current=args.create_metafile_snapshot(tarfile_size),
                history=args.history,
                files=merged_files,
            )

            metafile.to_file(self.directory_target / metafile.current.metafile_name)

            metafile.stats()

    def do_tar(
        self,
        merged_files: list[MetafileFileEntry],
        filename_target: pathlib.Path,
    ) -> int:
        tar_files = [
            entry.path
            for entry in merged_files
            if entry.verb in (EnumVerb.ADDED, EnumVerb.MODIFIED)
        ]

        directory_src = self.directory_src
        if self.backup_json.directory_name_include:
            directory_src = directory_src.parent
            dir_name = self.directory.name
            tar_files = [f"{dir_name}/{f}" for f in tar_files]

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_filename = pathlib.Path(temp_file.name)
            temp_file.write("\n".join(tar_files) + "\n")
        try:
            if sys.platform == "win32":
                compression = ["-zcf"]
            else:
                compression = ["--zstd", "-cf"]
            args = [
                "tar",
                "--files-from",
                str(temp_filename),
                *compression,
                str(filename_target),
            ]
            logger.debug(f"Calling: {' '.join(args)}")
            subprocess.run(args, cwd=directory_src, check=True)
            return filename_target.stat().st_size
        finally:
            temp_filename.unlink(missing_ok=True)


class TraverseZulup:
    def __init__(self) -> None:
        self.list_dir_zulup_json: list[DirectoryBackupJson] = []

    def get_zulup_entry(self, backup_name: str) -> DirectoryBackupJson:
        for entry in self.list_dir_zulup_json:
            if entry.backup_json.backup_name == backup_name:
                return entry
        raise ValueError(f"Backup '{backup_name}' not found")

    def get_traverse_backup(self, backup_name: str) -> DirectoryBackupJson:
        return self.get_zulup_entry(backup_name)

    def collect(self, directory: pathlib.Path) -> None:
        self._collect(directory)

    def _collect(self, directory: pathlib.Path) -> None:
        backup_path = directory / ZULUP_BACKUP_JSON
        scan_path = directory / ZULUP_SCAN_JSON

        if backup_path.exists() and scan_path.exists():
            raise ValueError(
                f"{directory}: '{ZULUP_BACKUP_JSON}' and '{ZULUP_SCAN_JSON}' must not coexist"
            )

        if backup_path.exists():
            backup_json = BackupJson.from_file(backup_path)
            self.list_dir_zulup_json.append(
                DirectoryBackupJson(directory=directory, backup_json=backup_json)
            )
            return

        if scan_path.exists():
            scan_json = ScanJson.from_file(scan_path)
            for directory_sub in sorted(directory.iterdir()):
                if not directory_sub.is_dir():
                    continue
                if self._matches_scan_pattern(directory_sub, scan_json.patterns):
                    self._collect(directory_sub)
            return

        for directory_sub in sorted(directory.iterdir()):
            if directory_sub.is_dir():
                self._collect(directory_sub)

    @staticmethod
    def _matches_scan_pattern(directory_sub: pathlib.Path, patterns: list[str]) -> bool:
        path_str = str(directory_sub)
        name = directory_sub.name
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(path_str, pattern):
                return True
        return False
