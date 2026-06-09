from __future__ import annotations

import abc
import dataclasses
import fnmatch
import json
import logging
import pathlib

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

    def __init__(self, filename_zulux_chmod_json: pathlib.Path) -> None:
        assert filename_zulux_chmod_json.name.endswith(ZULUX_CHMOD_JSON_SUFFIX), (
            f"Filename must end with '{ZULUX_CHMOD_JSON_SUFFIX}', "
            f"got: {filename_zulux_chmod_json.name!r}"
        )
        data = json.loads(filename_zulux_chmod_json.read_text())
        self._entries: list[_ZuluxJsonEntry] = [
            _ZuluxJsonEntry.from_dict(entry) for entry in data
        ]

    @abc.abstractmethod
    def chmod_file(self, filename: pathlib.Path, mode: str) -> None:
        """Apply mode (e.g. 'rwxr-xr-x') to filename."""

    @abc.abstractmethod
    def chown_file(self, filename: pathlib.Path, user: str, group: str) -> None:
        """Apply user and/or group ownership to filename."""

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
                    self.chown_file(directory, spec.user, spec.group)
                if spec.mode:
                    self.chmod_file(directory, spec.mode)
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
                    self.chown_file(pathlib.Path("."), spec.user, spec.group)
                if spec.mode:
                    self.chmod_file(pathlib.Path("."), spec.mode)
                return


class ZuluxTest(Zulux):
    """
    Test implementation of Zulux.

    chmod_file() and chown_file() accumulate results in memory.
    Call write_expected() to write the golden output file in the format:
        <user> : <group> : <mode> <rel_path>
    Directories are written with a trailing /.
    """

    def __init__(
        self,
        filename_zulux_chmod_json: pathlib.Path,
        filename_expected: pathlib.Path,
    ) -> None:
        super().__init__(filename_zulux_chmod_json)
        self._filename_expected = filename_expected
        # rel_path -> (user, group, mode)
        self._results: dict[str, tuple[str, str, str]] = {}
        # keys of paths that are directories (written with trailing / in output)
        self._dir_keys: set[str] = set()

    def chmod_file(self, filename: pathlib.Path, mode: str) -> None:
        key = filename.as_posix()
        user, group, _ = self._results.get(key, ("", "", ""))
        self._results[key] = (user, group, mode)

    def chown_file(self, filename: pathlib.Path, user: str, group: str) -> None:
        key = filename.as_posix()
        _, _, mode = self._results.get(key, ("", "", ""))
        self._results[key] = (user, group, mode)

    def apply_directory(self, directory: pathlib.Path) -> None:
        self._dir_keys.add(directory.as_posix())
        super().apply_directory(directory)

    def apply_directory_self(self) -> None:
        self._dir_keys.add(".")
        super().apply_directory_self()

    def write_expected(self) -> None:
        """Write accumulated results to the expected output file."""
        lines = [
            f"{user} : {group} : {mode} {rel_path + '/' if rel_path in self._dir_keys else rel_path}\n"
            for rel_path, (user, group, mode) in sorted(self._results.items())
        ]
        self._filename_expected.write_text("".join(lines))
