from __future__ import annotations

import logging
import os
import pathlib
import socket
import subprocess
import sys
import tempfile

from . import util_constants
from .util_backup_directory import BackupDirectory
from .util_json_metafile import (
    CurrentFileEntries,
    CurrentFileEntry,
    EnumVerb,
    Metafile,
    MetafileBackup,
    MetafileFileEntry,
    MetafileSnapshot,
)
from .util_json_zulup import BackupJson
from .util_logging import snapshot_logfile
from .util_traverse_zulup import DirectoryBackupJson

logger = logging.getLogger(__name__)


class TraverseBackup:
    def __init__(self, dir_zulup_json: DirectoryBackupJson) -> None:
        assert isinstance(dir_zulup_json, DirectoryBackupJson)
        self.dir_zulup_json = dir_zulup_json

    @property
    def directory_src(self) -> pathlib.Path:
        return self.dir_zulup_json.directory / self.backup_json.directory_src

    @property
    def directory_target(self) -> pathlib.Path:
        return pathlib.Path(self.backup_json.directory_target)

    @property
    def backup_json(self) -> BackupJson:
        return self.dir_zulup_json.backup_json

    @property
    def backup_directory(self) -> BackupDirectory:
        from zulup.util_backup_directory import BackupDirectory

        return BackupDirectory(
            directory=self.directory_target,
            backup_name=self.backup_json.backup_name,
        )

    @property
    def files(self) -> list[str]:
        ignore = self.dir_zulup_json.zulup_ignore
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

    def do_backup(self, full: bool, snapshot_datetime: str | None = None) -> None:
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

        context = self.backup_directory.build_run_context(
            full=full,
            snapshot_datetime=snapshot_datetime,
            directory_target=self.directory_target,
        )

        # Merge
        merged_files = self.current_files.merge_files(
            last_files=context.last_files,
            snapshot_datetime=context.snapshot_datetime,
        )

        logger.info(f"snapshot: {context.filename_tar}")
        with snapshot_logfile(
            filename_log=context.filename_tar.with_suffix(util_constants.LOGFILE_SUFFIX)
        ):
            tarfile_size = self.do_tar(
                merged_files=merged_files,
                filename_target=context.filename_tar,
            )

            metafile = Metafile(
                backup=MetafileBackup(
                    backup_name=self.backup_json.backup_name,
                    parent=str(self.directory_src),
                    hostname=socket.gethostname(),
                ),
                current=MetafileSnapshot(
                    snapshot_datetime=context.snapshot_datetime,
                    snapshot_type=context.snapshot_type,
                    snapshot_stem=context.filename_tar.stem,
                    tarfile_size=tarfile_size,
                ),
                history=context.history,
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
            dir_name = self.dir_zulup_json.directory.name
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
