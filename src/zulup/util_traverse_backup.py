from __future__ import annotations

import pathlib

from zulup.util_constants import ZULUP_JSON
from zulup.util_json_zulup import ZulupBackup, ZulupFilter
from zulup.util_traverse_zulup import DirectoryZulupJson


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
