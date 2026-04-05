from __future__ import annotations

import pathlib
import re

from zulup.util_constants import ZULUP_JSON
from zulup.util_json_zulup import ZulupBackup, ZulupFilterEntry
from zulup.util_traverse_zulup import DirectoryZulupJson


# TODO: Refactor
def _matches(entry: ZulupFilterEntry, name: str, rel_path: str) -> bool:
    value = name if entry.name is not None else rel_path
    pattern = entry.name if entry.name is not None else entry.path
    if pattern is None:
        return False
    if entry.matching == "literal":
        return value == pattern
    if entry.matching == "nocase":
        return value.lower() == pattern.lower()
    if entry.matching == "regexp":
        return re.match(pattern, value) is not None
    return False


# TODO: Refactor
def _is_excluded(filter_: list[ZulupFilterEntry], name: str, rel_path: str) -> bool:
    excluded = False
    for entry in filter_:
        if _matches(entry, name, rel_path):
            excluded = entry.logic == "exclude"
    return excluded


class TraverseBackup:
    def __init__(self, dir_zulup_json: DirectoryZulupJson) -> None:
        assert isinstance(dir_zulup_json, DirectoryZulupJson)
        assert dir_zulup_json.zulup_json.backup is not None
        self.dir_zulup_json = dir_zulup_json
        backup: ZulupBackup = dir_zulup_json.zulup_json.backup
        filter_ = backup.filter or []

        self.files: list[str] = []

        if backup.directory_name_include:
            prefix = dir_zulup_json.directory.name + "/"
        else:
            prefix = ""

        self._collect(self.directory_src, self.directory_src, prefix, filter_)
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
        filter_: list[ZulupFilterEntry],
    ) -> None:
        for directory_sub in sorted(directory.iterdir()):
            name = directory_sub.name
            rel_path = prefix + str(directory_sub.relative_to(directory_top))
            if directory_sub.is_dir():
                if not _is_excluded(filter_, name, rel_path):
                    self._collect(directory_sub, directory_top, prefix, filter_)
            elif directory_sub.is_file():
                if name == ZULUP_JSON:
                    continue
                if not _is_excluded(filter_, name, rel_path):
                    self.files.append(rel_path)
