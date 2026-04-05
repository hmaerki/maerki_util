from __future__ import annotations

import dataclasses
import pathlib

from zulup.util_constants import ZULUP_JSON
from zulup.util_json_zulup import ZulupJson


@dataclasses.dataclass(frozen=True)
class TraverseZulupEntry:
    directory: pathlib.Path
    zulup_json: ZulupJson


class TraverseZulup:
    def __init__(self, directory: pathlib.Path) -> None:
        self.directory = directory
        self.backups: list[TraverseZulupEntry] = []
        self._traverse(directory, remaining_depth=None)

    def get_zulup_entry(self, backup_name: str) -> TraverseZulupEntry:
        for entry in self.backups:
            assert entry.zulup_json.backup is not None
            if entry.zulup_json.backup.backup_name == backup_name:
                return entry
        raise ValueError(f"Backup '{backup_name}' not found")

    def get_traverse_backup(self, backup_name: str) -> TraverseBackup:
        from zulup.util_traverse_backup import TraverseBackup

        return TraverseBackup(self.get_zulup_entry(backup_name))

    def _traverse(self, directory: pathlib.Path, remaining_depth: int | None) -> None:
        zulup_json_path = directory / ZULUP_JSON
        if zulup_json_path.exists():
            zulup_json = ZulupJson.from_file(zulup_json_path)
            if zulup_json.backup is not None:
                self.backups.append(
                    TraverseZulupEntry(directory=directory, zulup_json=zulup_json)
                )
            if zulup_json.depth is not None:
                remaining_depth = zulup_json.depth

        if remaining_depth is not None:
            if remaining_depth <= 0:
                return
            remaining_depth -= 1

        for child in sorted(directory.iterdir()):
            if child.is_dir():
                self._traverse(child, remaining_depth)
