from __future__ import annotations

import dataclasses
import json
import pathlib


@dataclasses.dataclass(frozen=True)
class ZulupSelectEntry:
    tags: list[str]
    pattern: str | None = None
    text: str | None = None
    path: str | None = None


@dataclasses.dataclass(frozen=True)
class ZulupBackup:
    backup_name: str
    directory_target: str
    directory_src: str
    directory_name_include: bool
    select: list[ZulupSelectEntry] | None = None


@dataclasses.dataclass(frozen=True)
class ZulupJson:
    depth: int | None = None
    backup: ZulupBackup | None = None

    @staticmethod
    def from_file(filename: pathlib.Path) -> ZulupJson:
        data = json.loads(filename.read_text())
        backup = None
        if "backup" in data:
            backup_data = data["backup"]
            select = None
            if "select" in backup_data:
                select = [ZulupSelectEntry(**entry) for entry in backup_data["select"]]
            backup = ZulupBackup(
                backup_name=backup_data["backup_name"],
                directory_target=backup_data["directory_target"],
                directory_src=backup_data["directory_src"],
                directory_name_include=backup_data["directory_name_include"],
                select=select,
            )
        return ZulupJson(
            depth=data.get("depth"),
            backup=backup,
        )

    def to_file(self, filename: pathlib.Path) -> None:
        data: dict[str, object] = {}
        if self.depth is not None:
            data["depth"] = self.depth
        if self.backup is not None:
            backup_dict: dict[str, object] = {
                "backup_name": self.backup.backup_name,
                "directory_target": self.backup.directory_target,
                "directory_src": self.backup.directory_src,
                "directory_name_include": self.backup.directory_name_include,
            }
            if self.backup.select is not None:
                backup_dict["select"] = [
                    {
                        k: v
                        for k, v in dataclasses.asdict(entry).items()
                        if v is not None
                    }
                    for entry in self.backup.select
                ]
            data["backup"] = backup_dict
        filename.write_text(json.dumps(data, indent=4) + "\n")
