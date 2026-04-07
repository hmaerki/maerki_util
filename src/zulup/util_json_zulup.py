from __future__ import annotations

import dataclasses
import fnmatch
import json
import logging
import pathlib
import re

logger = logging.getLogger(__name__)

BACKUP_NAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


class ZulupIgnore(list[str]):
    """
    .gitignore-style ignore patterns based on fnmatch.

    Rules:
    - A pattern ending with `/` matches only directories; otherwise only files.
    - A pattern starting with `!` is an include (overrides a previous exclude).
    - A pattern containing `/` (other than a trailing `/`) is matched against
      the relative path; otherwise against the name only.
    - The first matching pattern wins.
    - By default (no match), the entry is included.
    """

    def is_included(self, name: str, rel_path: str, is_dir: bool) -> bool:
        for raw in self:
            pattern = raw
            include = False

            if pattern.startswith("!"):
                include = True
                pattern = pattern[1:]

            is_dir_pattern = pattern.endswith("/")
            if is_dir_pattern:
                pattern = pattern[:-1]

            if is_dir != is_dir_pattern:
                continue

            if "/" in pattern:
                matched = fnmatch.fnmatch(rel_path, pattern)
            else:
                matched = fnmatch.fnmatch(name, pattern)

            if matched:
                return include

        return True


@dataclasses.dataclass(frozen=True)
class ZulupBackup:
    backup_name: str
    directory_target: str
    directory_src: str
    directory_name_include: bool
    ignore: list[str] | None = None

    def __post_init__(self) -> None:
        if not BACKUP_NAME_RE.match(self.backup_name):
            raise ValueError(
                f"backup_name '{self.backup_name}' does not match {BACKUP_NAME_RE.pattern}!"
            )


@dataclasses.dataclass(frozen=True)
class ZulupJson:
    backup: ZulupBackup

    def __post_init__(self) -> None:
        assert isinstance(self.backup, ZulupBackup)

    @staticmethod
    def from_file(filename: pathlib.Path) -> ZulupJson:
        try:
            data = json.loads(filename.read_text())
        except json.JSONDecodeError as e:
            msg = f"{filename}: {e}"
            logger.error(msg)
            raise ValueError(msg) from e

        ignore: list[str] | None = data.get("ignore")
        backup = ZulupBackup(
            backup_name=data["backup_name"],
            directory_target=data["directory_target"],
            directory_src=data["directory_src"],
            directory_name_include=data["directory_name_include"],
            ignore=ignore,
        )
        return ZulupJson(backup=backup)

    def to_file(self, filename: pathlib.Path) -> None:
        data: dict[str, object] = {
            "backup_name": self.backup.backup_name,
            "directory_target": self.backup.directory_target,
            "directory_src": self.backup.directory_src,
            "directory_name_include": self.backup.directory_name_include,
        }
        if self.backup.ignore is not None:
            data["ignore"] = self.backup.ignore
        filename.write_text(json.dumps(data, indent=4) + "\n")


@dataclasses.dataclass(frozen=True)
class ZulupScanJson:
    patterns: list[str]

    def __post_init__(self) -> None:
        assert isinstance(self.patterns, list)
        for pattern in self.patterns:
            assert isinstance(pattern, str)

    @staticmethod
    def from_file(filename: pathlib.Path) -> ZulupScanJson:
        try:
            data = json.loads(filename.read_text())
        except json.JSONDecodeError as e:
            msg = f"{filename}: {e}"
            logger.error(msg)
            raise ValueError(msg) from e

        if not isinstance(data, list):
            raise ValueError(f"{filename}: expected JSON list")

        for index, value in enumerate(data):
            if not isinstance(value, str):
                raise ValueError(f"{filename}: index {index}: expected string")

        return ZulupScanJson(patterns=data)

    def to_file(self, filename: pathlib.Path) -> None:
        filename.write_text(json.dumps(self.patterns, indent=4) + "\n")
