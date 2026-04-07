from __future__ import annotations

import dataclasses
import fnmatch
import logging
import pathlib
import typing

from zulup.util_constants import ZULUP_BACKUP_JSON, ZULUP_SCAN_JSON
from zulup.util_json_zulup import ZulupBackupJson, ZulupIgnore, ZulupScanJson

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from zulup.util_traverse_backup import TraverseBackup


@dataclasses.dataclass(frozen=True)
class DirectoryZulupJson:
    directory: pathlib.Path
    backup_json: ZulupBackupJson

    def __post_init__(self) -> None:
        assert isinstance(self.directory, pathlib.Path)
        assert isinstance(self.backup_json, ZulupBackupJson)

    @property
    def zulup_ignore(self) -> ZulupIgnore:
        return ZulupIgnore(self.backup_json.ignore or [])


class TraverseZulup:
    def __init__(self) -> None:
        self.list_dir_zulup_json: list[DirectoryZulupJson] = []

    def get_zulup_entry(self, backup_name: str) -> DirectoryZulupJson:
        for entry in self.list_dir_zulup_json:
            if entry.backup_json.backup_name == backup_name:
                return entry
        raise ValueError(f"Backup '{backup_name}' not found")

    def get_traverse_backup(self, backup_name: str) -> TraverseBackup:
        from zulup.util_traverse_backup import TraverseBackup

        return TraverseBackup(self.get_zulup_entry(backup_name))

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
            backup_json = ZulupBackupJson.from_file(backup_path)
            self.list_dir_zulup_json.append(
                DirectoryZulupJson(directory=directory, backup_json=backup_json)
            )
            return

        if scan_path.exists():
            scan_json = ZulupScanJson.from_file(scan_path)
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
