from __future__ import annotations

import pathlib

from .util_backup_directory import BackupDirectory
from .util_constants import ZULUP_JSON
from .util_json_zulup import ZulupBackup, ZulupFilter
from .util_traverse_zulup import DirectoryZulupJson


class TraverseBackup:
    def __init__(self, dir_zulup_json: DirectoryZulupJson) -> None:
        assert isinstance(dir_zulup_json, DirectoryZulupJson)
        assert dir_zulup_json.zulup_json.backup is not None
        self.dir_zulup_json = dir_zulup_json
        backup: ZulupBackup = dir_zulup_json.zulup_json.backup
        filter = backup.filter or ZulupFilter([])

        self.files: list[str] = []

        if backup.directory_name_include:
            prefix = dir_zulup_json.directory.name + "/"
        else:
            prefix = ""

        self._collect(
            directory=self.directory_src,
            directory_top=self.directory_src,
            prefix=prefix,
            filter=filter,
        )
        self.files.sort()

    @property
    def directory_src(self) -> pathlib.Path:
        return self.dir_zulup_json.directory / self.backup.directory_src

    @property
    def backup(self) -> ZulupBackup:
        assert self.dir_zulup_json.zulup_json.backup is not None
        return self.dir_zulup_json.zulup_json.backup

    @property
    def backup_directory(self) -> BackupDirectory:
        from zulup.util_backup_directory import BackupDirectory

        return BackupDirectory(
            directory=self.directory_src,
            backup_name=self.backup.backup_name,
        )

    def verify_history(self) -> None:
        backup_directory = self.backup_directory
        if backup_directory.last_snapshot is not None:
            metafile = backup_directory.last_snapshot.metafile
            backup_directory.verify_history(metafile=metafile)

    def do_backup(self, full: bool) -> None:
        """
        See AGENTS.md

        * Merge `last_metafile` with `current_filelist` into `new_metafile`. In this step the `verb` will be updated:
            * `added`: If the file is new.
            * `removed`: if the file is gone.
            * `untouched`: If the file size and modification time have not changed.
            * `modified`: else
        * Create a file list as input into `tar --files-from`: All files which are `added` or `modified`.
        * Call `tar --zstd --files-from ... -cf <directory_target>/<snapshot_stem>.tgz_tmp`.
        * Calculate sha256 from `<directory_target>/<snapshot_stem>.tgz_tmp` and add it to `backup/tar_checksum` of `new_metafile`.
        * Store `new_metafile` in `<directory_target>/<snapshot_stem>.json`.
        * Rename `<snapshot_stem>.tgz_tmp` to `<snapshot_stem>.tgz`
        """
        pass

    def _collect(
        self,
        directory: pathlib.Path,
        directory_top: pathlib.Path,
        prefix: str,
        filter: ZulupFilter,
    ) -> None:
        assert isinstance(directory, pathlib.Path)
        assert isinstance(directory_top, pathlib.Path)
        assert isinstance(prefix, str)
        assert isinstance(filter, ZulupFilter)

        for directory_sub in sorted(directory.iterdir()):
            name = directory_sub.name
            rel_path = prefix + str(directory_sub.relative_to(directory_top))
            if directory_sub.is_dir():
                if not filter.is_excluded(name, rel_path):
                    self._collect(directory_sub, directory_top, prefix, filter)
            elif directory_sub.is_file():
                if name == ZULUP_JSON:
                    continue
                if not filter.is_excluded(name, rel_path):
                    self.files.append(rel_path)


class ListTraverseBackup(list[TraverseBackup]):
    def verify_history(self) -> None:
        for traverse_backup in self:
            traverse_backup.verify_history()

    def do_backup(self, full: bool) -> None:
        for traverse_backup in self:
            traverse_backup.do_backup(full=full)
