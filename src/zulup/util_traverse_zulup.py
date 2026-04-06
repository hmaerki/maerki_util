from __future__ import annotations

import dataclasses
import logging
import pathlib
import typing

from zulup.util_constants import ZULUP_JSON
from zulup.util_json_zulup import ZulupJson

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from zulup.util_traverse_backup import TraverseBackup


@dataclasses.dataclass(frozen=True)
class DirectoryZulupJson:
    directory: pathlib.Path
    zulup_json: ZulupJson

    def __post_init__(self) -> None:
        assert isinstance(self.directory, pathlib.Path)
        assert isinstance(self.zulup_json, ZulupJson)


class TraverseZulup:
    def __init__(self) -> None:
        self.list_dir_zulup_json: list[DirectoryZulupJson] = []

    def get_zulup_entry(self, backup_name: str) -> DirectoryZulupJson:
        for entry in self.list_dir_zulup_json:
            assert entry.zulup_json.backup is not None
            if entry.zulup_json.backup.backup_name == backup_name:
                return entry
        raise ValueError(f"Backup '{backup_name}' not found")

    def get_traverse_backup(self, backup_name: str) -> TraverseBackup:
        from zulup.util_traverse_backup import TraverseBackup

        return TraverseBackup(self.get_zulup_entry(backup_name))

    def collect(self, directory: pathlib.Path) -> None:
        self._collect(directory, remaining_depth=None)

    def _collect(self, directory: pathlib.Path, remaining_depth: int | None) -> None:
        zulup_json_path = directory / ZULUP_JSON
        if zulup_json_path.exists():
            zulup_json = ZulupJson.from_file(zulup_json_path)
            if zulup_json.backup is not None:
                self.list_dir_zulup_json.append(
                    DirectoryZulupJson(directory=directory, zulup_json=zulup_json)
                )
                return
            if zulup_json.depth is not None:
                remaining_depth = zulup_json.depth

        if remaining_depth is not None:
            if remaining_depth <= 0:
                return
            remaining_depth -= 1

        directories = sorted(directory.iterdir())
        for directory_sub in directories:
            if directory_sub.is_dir():
                self._collect(directory_sub, remaining_depth)
