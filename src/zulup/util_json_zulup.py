from __future__ import annotations

import dataclasses
import fnmatch
import json
import logging
import pathlib
import re
from typing import TYPE_CHECKING

from zulup.util_constants import (
    DIRECTORY_NAME_TOKEN,
    ZULUP_BACKUP_DEFAULTS_JSON,
    ZULUP_BACKUP_JSON,
)

if TYPE_CHECKING:
    from zulup.util_backup_directory import BackupDirectory

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
class BackupJson:
    backup_name: str
    directory_target: str
    directory_src: str
    directory_name_include: bool
    ignore: list[str] | None = None

    def __post_init__(self) -> None:
        if self.backup_name == DIRECTORY_NAME_TOKEN:
            return
        if not BACKUP_NAME_RE.match(self.backup_name):
            raise ValueError(
                f"backup_name '{self.backup_name}' does not match {BACKUP_NAME_RE.pattern}!"
            )

    @staticmethod
    def from_file(filename: pathlib.Path) -> BackupJson:
        def _read_json_dict(file_path: pathlib.Path) -> dict[str, str | list]:
            try:
                data = json.loads(file_path.read_text())
            except json.JSONDecodeError as e:
                msg = f"{file_path}: {e}"
                logger.error(msg)
                raise ValueError(msg) from e
            if not isinstance(data, dict):
                msg = f"{file_path}: expected JSON object"
                logger.error(msg)
                raise ValueError(msg)
            return data

        kwargs = _read_json_dict(filename)

        # Apply optional global defaults only to real zulup_backup.json files.
        if filename.name == ZULUP_BACKUP_JSON:
            filename_defaults = pathlib.Path.home() / ZULUP_BACKUP_DEFAULTS_JSON
            if filename_defaults.is_file():
                defaults = _read_json_dict(filename_defaults)
                kwargs = {**defaults, **kwargs}

        b = BackupJson(**kwargs)  # type: ignore
        if b.backup_name == DIRECTORY_NAME_TOKEN:
            return dataclasses.replace(b, backup_name=filename.parent.name)
        return b

    def to_file(self, filename: pathlib.Path) -> None:
        data: dict[str, object] = {
            "backup_name": self.backup_name,
            "directory_target": self.directory_target,
            "directory_src": self.directory_src,
            "directory_name_include": self.directory_name_include,
        }
        if self.ignore is not None:
            data["ignore"] = self.ignore
        filename.write_text(json.dumps(data, indent=4) + "\n")

    @property
    def backup_directory(self) -> BackupDirectory:
        from zulup.util_backup_directory import BackupDirectory

        return BackupDirectory(
            directory=pathlib.Path(self.directory_target),
            backup_name=self.backup_name,
        )


@dataclasses.dataclass(frozen=True)
class ScanJson:
    patterns: list[str]

    def __post_init__(self) -> None:
        assert isinstance(self.patterns, list)
        for pattern in self.patterns:
            assert isinstance(pattern, str)

    @staticmethod
    def from_file(filename: pathlib.Path) -> ScanJson:
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

        return ScanJson(patterns=data)

    def to_file(self, filename: pathlib.Path) -> None:
        filename.write_text(json.dumps(self.patterns, indent=4) + "\n")
