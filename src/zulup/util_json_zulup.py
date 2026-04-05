from __future__ import annotations

import dataclasses
import enum
import json
import pathlib
import re

from zulup.util_json import check_enum

BACKUP_NAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


class EnumMatching(enum.StrEnum):
    LITERAL = "literal"
    NOCASE = "nocase"
    REGEXP = "regexp"


class EnumLogic(enum.StrEnum):
    EXCLUDE = "exclude"
    INCLUDE = "include"


class EnumKind(enum.StrEnum):
    FILE = "file"
    DIRECTORY = "directory"


@dataclasses.dataclass(frozen=True)
class ZulupFilter:
    name: str | None = None
    path: str | None = None
    matching: str = EnumMatching.LITERAL.value
    kind: str = EnumKind.FILE.value
    logic: str = EnumLogic.EXCLUDE.value

    def __post_init__(self) -> None:
        check_enum(EnumMatching, self.matching)
        check_enum(EnumKind, self.kind)
        check_enum(EnumLogic, self.logic)
        assert (self.name is None) is not (self.path is None), (
            "Ether 'name' or 'path' must be specified!"
        )

    def matches(self, path: pathlib.Path, is_dir: bool) -> bool:
        assert isinstance(path, pathlib.Path)
        assert isinstance(is_dir, bool)

        if is_dir and self.kind != EnumKind.DIRECTORY:
            return False
        if not is_dir and self.kind != EnumKind.FILE:
            return False

        name_or_path = path.name
        pattern = self.name
        if self.path is not None:
            name_or_path = str(path)
            pattern = self.path
        assert pattern is not None

        if self.matching == EnumMatching.LITERAL:
            return name_or_path == pattern
        if self.matching == EnumMatching.NOCASE:
            return name_or_path.lower() == pattern.lower()
        if self.matching == EnumMatching.REGEXP:
            return re.match(pattern, name_or_path) is not None
        return False


class ZulupFilters(list[ZulupFilter]):
    def is_included(self, path: pathlib.Path, is_dir: bool) -> bool:
        for entry in self:
            if entry.matches(path, is_dir):
                return entry.logic == EnumLogic.INCLUDE
        return True


@dataclasses.dataclass(frozen=True)
class ZulupBackup:
    backup_name: str
    directory_target: str
    directory_src: str
    directory_name_include: bool
    filters: ZulupFilters | None = None

    def __post_init__(self) -> None:
        if not BACKUP_NAME_RE.match(self.backup_name):
            raise ValueError(
                f"backup_name '{self.backup_name}' does not match {BACKUP_NAME_RE.pattern}!"
            )


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
            filters: ZulupFilters | None = None
            if "filters" in backup_data:
                filters = ZulupFilters(
                    [ZulupFilter(**entry) for entry in backup_data["filters"]]
                )
            backup = ZulupBackup(
                backup_name=backup_data["backup_name"],
                directory_target=backup_data["directory_target"],
                directory_src=backup_data["directory_src"],
                directory_name_include=backup_data["directory_name_include"],
                filters=filters,
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
            if self.backup.filters is not None:
                backup_dict["filters"] = [
                    {
                        k: v
                        for k, v in dataclasses.asdict(entry).items()
                        if v is not None
                        and not (k == "matching" and v == "literal")
                        and not (k == "kind" and v == "file")
                        and not (k == "logic" and v == "exclude")
                    }
                    for entry in self.backup.filters
                ]
            data["backup"] = backup_dict
        filename.write_text(json.dumps(data, indent=4) + "\n")
