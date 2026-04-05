from __future__ import annotations

import pathlib
import re

from zulup.util_constants import ZULUP_JSON
from zulup.util_json_zulup import ZulupBackup, ZulupFilterEntry
from zulup.util_traverse_zulup import TraverseZulupJson


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
    def __init__(self, t_zulup_json: TraverseZulupJson) -> None:
        assert isinstance(t_zulup_json, TraverseZulupJson)
        assert t_zulup_json.zulup_json.backup is not None
        self.t_zulup_json = t_zulup_json
        self.backup: ZulupBackup = t_zulup_json.zulup_json.backup
        directory_src = t_zulup_json.directory / self.backup.directory_src
        filter_ = self.backup.filter or []

        self.files: list[str] = []

        if self.backup.directory_name_include:
            prefix = t_zulup_json.directory.name + "/"
        else:
            prefix = ""

        self._collect(directory_src, directory_src, prefix, filter_)
        self.files.sort()

    def _collect(
        self,
        directory: pathlib.Path,
        root: pathlib.Path,
        prefix: str,
        filter_: list[ZulupFilterEntry],
    ) -> None:
        for child in sorted(directory.iterdir()):
            name = child.name
            rel_path = prefix + str(child.relative_to(root))
            if child.is_dir():
                if not _is_excluded(filter_, name, rel_path):
                    self._collect(child, root, prefix, filter_)
            elif child.is_file():
                if name == ZULUP_JSON:
                    continue
                if not _is_excluded(filter_, name, rel_path):
                    self.files.append(rel_path)
