from __future__ import annotations

import abc
import dataclasses
import fnmatch
import json
import logging
import pathlib
import typing

from zulux.util_constants import ZULUX_CHMOD_JSON_SUFFIX

logger = logging.getLogger(__file__)


def _matches_patterns(patterns: list[str], name: str, rel_path: str) -> bool:
    """
    Single ordered patterns list; first matching pattern decides.
    A pattern starting with '!' means exclude; without '!' means include.
    A trailing '/' marks a directory pattern and is stripped before matching.
    A pattern containing '/' (other than trailing) is matched against rel_path;
    otherwise against name only.
    Default (no match): not selected.
    """
    for raw in patterns:
        exclude = raw.startswith("!")
        pattern = raw[1:] if exclude else raw

        # Strip trailing / (directory marker, not part of the fnmatch glob)
        if pattern.endswith("/"):
            pattern = pattern[:-1]

        if "/" in pattern:
            matched = fnmatch.fnmatch(rel_path, pattern)
        else:
            matched = fnmatch.fnmatch(name, pattern)

        if matched:
            return not exclude

    return False


@dataclasses.dataclass(frozen=True)
class _ChmodSpec:
    user: str
    group: str
    mode: str

    @staticmethod
    def parse(chmod_str: str) -> _ChmodSpec:
        parts = chmod_str.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"chmod string must contain exactly 2 ':' characters, got: {chmod_str!r}"
            )
        return _ChmodSpec(user=parts[0], group=parts[1], mode=parts[2])


@dataclasses.dataclass(frozen=True)
class _FilesEntry:
    patterns: list[str]
    chmod_spec: _ChmodSpec

    @staticmethod
    def from_dict(data: dict) -> _FilesEntry:
        patterns = data.get("patterns", [])
        chmod_spec = _ChmodSpec.parse(data["chmod"])
        return _FilesEntry(patterns=patterns, chmod_spec=chmod_spec)


@dataclasses.dataclass(frozen=True)
class _ZuluxJsonEntry:
    files: _FilesEntry | None
    directories: _FilesEntry | None
    directory_self_chmod: _ChmodSpec | None

    @staticmethod
    def from_dict(data: dict) -> _ZuluxJsonEntry:
        files = _FilesEntry.from_dict(data["files"]) if "files" in data else None
        directories = (
            _FilesEntry.from_dict(data["directories"])
            if "directories" in data
            else None
        )
        directory_self_chmod = (
            _ChmodSpec.parse(data["directory_self"]["chmod"])
            if "directory_self" in data
            else None
        )
        return _ZuluxJsonEntry(
            files=files,
            directories=directories,
            directory_self_chmod=directory_self_chmod,
        )


class Zulux(abc.ABC):
    """
    Base class for applying zulux permission rules from a *zulux_chmod.json file.

    Subclasses implement chmod_file() and chown_file() to perform the actual
    permission change (production) or record results (testing).
    """

    def __init__(self, zulux_json: pathlib.Path | list[typing.Any]) -> None:
        if isinstance(zulux_json, pathlib.Path):
            assert zulux_json.name.endswith(ZULUX_CHMOD_JSON_SUFFIX), (
                f"Filename must end with '{ZULUX_CHMOD_JSON_SUFFIX}', "
                f"got: {zulux_json.name!r}"
            )
            data = json.loads(zulux_json.read_text())
        else:
            data = zulux_json
        self._entries: list[_ZuluxJsonEntry] = [
            _ZuluxJsonEntry.from_dict(entry) for entry in data
        ]

    @abc.abstractmethod
    def chmod_file(self, filename: pathlib.Path, mode: str) -> None:
        """Apply mode (e.g. 'rwxr-xr-x') to a file."""

    @abc.abstractmethod
    def chown_file(self, filename: pathlib.Path, user: str, group: str) -> None:
        """Apply user and/or group ownership to a file."""

    @abc.abstractmethod
    def chmod_directory(self, directory: pathlib.Path, mode: str) -> None:
        """Apply mode (e.g. 'rwxr-xr-x') to a directory."""

    @abc.abstractmethod
    def chown_directory(self, directory: pathlib.Path, user: str, group: str) -> None:
        """Apply user and/or group ownership to a directory."""

    def apply_file(self, filename: pathlib.Path) -> None:
        """
        Evaluate filename against all entries in *zulux_chmod.json (top to bottom).
        The first matching entry is applied; remaining entries are skipped.
        filename must be a relative path (e.g. pathlib.Path('wikiwiki/x/run.cgi')).
        If no entry matches, permissions are NOT changed.
        """
        name = filename.name
        rel_path = filename.as_posix()

        for entry in self._entries:
            if entry.files is None:
                continue
            if _matches_patterns(entry.files.patterns, name, rel_path):
                spec = entry.files.chmod_spec
                if spec.user or spec.group:
                    self.chown_file(filename, spec.user, spec.group)
                if spec.mode:
                    self.chmod_file(filename, spec.mode)
                return  # first match wins

    def apply_directory(self, directory: pathlib.Path) -> None:
        """
        Evaluate directory against all 'directories' entries (top to bottom).
        directory must be a relative path without trailing slash.
        If no entry matches, permissions are NOT changed.
        """
        name = directory.name
        rel_path = directory.as_posix()

        for entry in self._entries:
            if entry.directories is None:
                continue
            if _matches_patterns(entry.directories.patterns, name, rel_path):
                spec = entry.directories.chmod_spec
                if spec.user or spec.group:
                    self.chown_directory(directory, spec.user, spec.group)
                if spec.mode:
                    self.chmod_directory(directory, spec.mode)
                return  # first match wins

    def apply_directory_self(self) -> None:
        """
        Apply the 'directory_self' entry (if present) to the directory that
        contains *zulux_chmod.json.  Uses pathlib.Path('.') as the target path.
        """
        for entry in self._entries:
            if entry.directory_self_chmod is not None:
                spec = entry.directory_self_chmod
                if spec.user or spec.group:
                    self.chown_directory(pathlib.Path("."), spec.user, spec.group)
                if spec.mode:
                    self.chmod_directory(pathlib.Path("."), spec.mode)
                return


class ZuluxTest(Zulux):
    """
    Test implementation of Zulux.

    Each chmod/chown call is written immediately to f_expected.
    Output format - one command per line:
        chown user:group path
        chmod mode path
    Directories are written with a trailing /.
    """

    def __init__(
        self,
        zulux_json: pathlib.Path | list[typing.Any],
        f_expected: typing.IO[str],
    ) -> None:
        super().__init__(zulux_json)
        self._f_expected = f_expected

    def chmod_file(self, filename: pathlib.Path, mode: str) -> None:
        self._write(f"chmod {mode}", filename, suffix="")

    def chown_file(self, filename: pathlib.Path, user: str, group: str) -> None:
        self._write(f"chown {user}:{group}", filename, suffix="")

    def chmod_directory(self, directory: pathlib.Path, mode: str) -> None:
        self._write(f"chmod {mode}", directory, suffix="/")

    def chown_directory(self, directory: pathlib.Path, user: str, group: str) -> None:
        self._write(f"chown {user}:{group}", directory, suffix="/")

    def _write(self, method: str, filename: pathlib.Path, *, suffix: str) -> None:
        self._f_expected.write(f"{method:<24s} {filename.as_posix()}{suffix}\n")


class ZuluxReal(Zulux):
    """
    Production implementation of Zulux.

    Applies permissions to real files and directories using os.chmod / os.chown.
    User and group names are resolved to numeric IDs via the pwd/grp modules.
    """

    def __init__(
        self,
        zulux_json: pathlib.Path,
        directory_root: pathlib.Path,
    ) -> None:
        super().__init__(zulux_json)
        self._directory_root = directory_root

    def _resolve_ids(self, user: str, group: str) -> tuple[int, int]:
        import grp
        import pwd

        uid = pwd.getpwnam(user).pw_uid if user else -1
        gid = grp.getgrnam(group).gr_gid if group else -1
        return uid, gid

    def _mode_to_int(self, mode: str) -> int:
        """Convert 'rwxr-xr-x' (9-char) to an integer mode."""
        bits = [
            0o400,
            0o200,
            0o100,
            0o040,
            0o020,
            0o010,
            0o004,
            0o002,
            0o001,
        ]
        result = 0
        for bit, ch in zip(bits, mode):
            if ch != "-":
                result |= bit
        return result

    def chmod_file(self, filename: pathlib.Path, mode: str) -> None:
        path = self._directory_root / filename
        logger.debug("chmod %s %s", mode, path)
        path.chmod(self._mode_to_int(mode))

    def chown_file(self, filename: pathlib.Path, user: str, group: str) -> None:
        path = self._directory_root / filename
        uid, gid = self._resolve_ids(user, group)
        logger.debug("chown %s:%s %s", user, group, path)
        import os

        os.chown(path, uid, gid)

    def chmod_directory(self, directory: pathlib.Path, mode: str) -> None:
        path = self._directory_root / directory
        logger.debug("chmod %s %s/", mode, path)
        path.chmod(self._mode_to_int(mode))

    def chown_directory(self, directory: pathlib.Path, user: str, group: str) -> None:
        path = self._directory_root / directory
        uid, gid = self._resolve_ids(user, group)
        logger.debug("chown %s:%s %s/", user, group, path)
        import os

        os.chown(path, uid, gid)
