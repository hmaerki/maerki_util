from __future__ import annotations

import json
import pathlib
from typing import TYPE_CHECKING

from zulup import util_constants

if TYPE_CHECKING:
    from zulup.util_backup_directory import BackupDirectory
    from zulup.util_traverse_zulup import DirectoryBackupJson


class TtestProjectDirectory:
    NAME = "project_demo"

    def __init__(self, tmp_path: pathlib.Path) -> None:
        directory_src = tmp_path / "src"
        directory_src.mkdir(exist_ok=True)
        self.src = directory_src / self.NAME
        self.src.mkdir()
        self.target = tmp_path / "target"

    def create_file(self, filename: str, content: str) -> pathlib.Path:
        file_path = self.src / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    def create_backup_json(
        self,
        directory_name_include: bool,
        ignore: list[str],
    ) -> pathlib.Path:
        backup_json = {
            "backup_name": self.src.name,
            "directory_target": str(self.target),
            "directory_src": ".",
            "directory_name_include": directory_name_include,
            "ignore": ignore,
        }
        return self.create_file(
            util_constants.ZULUP_BACKUP_JSON, json.dumps(backup_json, indent=4) + "\n"
        )

    def create_scan_json(self, patterns: list[str]) -> pathlib.Path:
        return self.create_file(
            util_constants.ZULUP_SCAN_JSON, json.dumps(patterns, indent=4) + "\n"
        )

    def get_directory_backup_json(self) -> DirectoryBackupJson:
        from zulup.util_traverse_zulup import TraverseZulup

        traverse = TraverseZulup()
        traverse.collect(self.src)
        return traverse.get_traverse_backup(self.src.name)

    def get_backup_directory(self) -> BackupDirectory:
        from zulup.util_backup_directory import BackupDirectory

        return BackupDirectory(self.target, self.NAME)

    def do_backup(
        self, full: bool = False, snapshot_datetime: str | None = None
    ) -> None:
        backup = self.get_directory_backup_json()
        backup.do_backup(
            full=full,
            snapshot_datetime=snapshot_datetime,
        )
