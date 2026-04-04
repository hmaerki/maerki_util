from __future__ import annotations

import pathlib
import re

from zulup.util_json_zulup import ZulupBackup, ZulupSelectEntry
from zulup.util_traverse_zulup import TraverseZulupEntry

ZULUP_JSON = "zulup.json"


def _matches(entry: ZulupSelectEntry, name: str, rel_path: str) -> bool:
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


def _is_excluded(select: list[ZulupSelectEntry], name: str, rel_path: str) -> bool:
    excluded = False
    for entry in select:
        if _matches(entry, name, rel_path):
            excluded = entry.logic == "exclude"
    return excluded


class TraverseBackup:
    def __init__(self, entry: TraverseZulupEntry) -> None:
        assert entry.zulup_json.backup is not None
        backup: ZulupBackup = entry.zulup_json.backup
        directory_src = entry.directory / backup.directory_src
        select = backup.select or []

        self.files: list[str] = []

        if backup.directory_name_include:
            prefix = entry.directory.name + "/"
        else:
            prefix = ""

        self._traverse(directory_src, directory_src, prefix, select)
        self.files.sort()

    def _traverse(
        self,
        directory: pathlib.Path,
        root: pathlib.Path,
        prefix: str,
        select: list[ZulupSelectEntry],
    ) -> None:
        for child in sorted(directory.iterdir()):
            name = child.name
            rel_path = prefix + str(child.relative_to(root))
            if child.is_dir():
                if not _is_excluded(select, name, rel_path):
                    self._traverse(child, root, prefix, select)
            elif child.is_file():
                if name == ZULUP_JSON:
                    continue
                if not _is_excluded(select, name, rel_path):
                    self.files.append(rel_path)
