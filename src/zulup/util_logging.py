from __future__ import annotations

import logging
import pathlib
import typing
from contextlib import contextmanager


@contextmanager
def snapshot_logfile(filename_log: pathlib.Path) -> typing.Iterator[None]:
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler(filename_log, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root_logger.addHandler(file_handler)

    try:
        yield
    finally:
        root_logger.removeHandler(file_handler)
        file_handler.close()
