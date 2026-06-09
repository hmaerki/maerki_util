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
    A pattern containing '/' (other than trailing) is matched against rel_path;
    otherwise against name only.
    Default (no match): not selected.
    """
    for raw in patterns:
        exclude = raw.startswith("!")
        pattern = raw[1:] if exclude else raw

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

    @staticmethod
    def from_dict(data: dict) -> _ZuluxJsonEntry:
        files = _FilesEntry.from_dict(data["files"]) if "files" in data else None
        return _ZuluxJsonEntry(files=files)


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


class ZuluxTest(Zulux):
    """
    Test implementation of Zulux.

    chmod_file() and chown_file() accumulate results in memory.
    Call write_expected() to write the golden output file in the format:
        <user> : <group> : <mode> <rel_path>
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

    def chmod_file(self, filename: pathlib.Path, mode: str) -> None:
        key = filename.as_posix()
        user, group, _ = self._results.get(key, ("", "", ""))
        self._results[key] = (user, group, mode)

    def chown_file(self, filename: pathlib.Path, user: str, group: str) -> None:
        key = filename.as_posix()
        _, _, mode = self._results.get(key, ("", "", ""))
        self._results[key] = (user, group, mode)

    def write_expected(self) -> None:
        """Write accumulated results to the expected output file."""
        lines = [
            f"{user} : {group} : {mode} {rel_path}\n"
            for rel_path, (user, group, mode) in sorted(self._results.items())
        ]
        self._filename_expected.write_text("".join(lines))
