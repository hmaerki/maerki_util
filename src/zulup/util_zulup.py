from __future__ import annotations

import logging
import pathlib
import time

from zulup.util_traverse_backup import TraverseBackup
from zulup.util_traverse_zulup import TraverseZulup

logger = logging.getLogger(__file__)


class Zulup:
    def __init__(self) -> None:
        self.begin_s = time.monotonic()

    @property
    def duration_s(self) -> float:
        return time.monotonic() - self.begin_s

    def log_duration(self, tag: str) -> None:
        logger.debug(f"{tag}: {self.duration_s:0.3f}s.")

    def traverse_directories(
        self,
        directories: list[pathlib.Path],
    ) -> list[TraverseBackup]:
        traverse = TraverseZulup()
        for directory in directories:
            traverse.collect(directory=directory)

        return [TraverseBackup(z) for z in traverse.list_dir_zulup_json]

    def verify(self, list_traverse_backup: list[TraverseBackup]) -> None:
        for traverse_backup in list_traverse_backup:
            traverse_backup.files
        pass
