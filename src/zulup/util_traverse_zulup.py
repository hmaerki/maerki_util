from __future__ import annotations

import dataclasses
import pathlib

from zulup.util_json_zulup import ZulupJson

ZULUP_JSON = "zulup.json"


@dataclasses.dataclass(frozen=True)
class TraverseZulupEntry:
    directory: pathlib.Path
    zulup_json: ZulupJson


class TraverseZulup:
    def __init__(self, directory: pathlib.Path) -> None:
        self.directory = directory
        self.backups: list[TraverseZulupEntry] = []
        self._traverse(directory, remaining_depth=None)

    def _traverse(self, directory: pathlib.Path, remaining_depth: int | None) -> None:
        zulup_json_path = directory / ZULUP_JSON
        if zulup_json_path.exists():
            zulup_json = ZulupJson.from_file(zulup_json_path)
            if zulup_json.backup is not None:
                self.backups.append(
                    TraverseZulupEntry(directory=directory, zulup_json=zulup_json)
                )
            if zulup_json.depth is not None:
                remaining_depth = zulup_json.depth

        if remaining_depth is not None:
            if remaining_depth <= 0:
                return
            remaining_depth -= 1

        for child in sorted(directory.iterdir()):
            if child.is_dir():
                self._traverse(child, remaining_depth)
