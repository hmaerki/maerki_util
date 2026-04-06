from __future__ import annotations

import contextlib
import logging
import subprocess
import sys
from collections.abc import Iterator

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def systemd_inhibit() -> Iterator[None]:
    process: subprocess.Popen[bytes] | None = None

    if sys.platform == "linux":
        import ctypes
        import signal

        libc = ctypes.CDLL("libc.so.6")
        PR_SET_PDEATHSIG = 1  # noqa: N806

        def set_death_signal() -> None:
            libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM)

        cmd = [
            "systemd-inhibit",
            "--who=zulup",
            "--what=shutdown:sleep",
            "--why=Backup in progress",
            "sleep",
            "infinity",
        ]
        try:
            process = subprocess.Popen(cmd, preexec_fn=set_death_signal)
            logger.debug("systemd-inhibit started (pid %d)", process.pid)
        except FileNotFoundError:
            logger.warning("systemd-inhibit not found, skipping inhibit")

    try:
        yield
    finally:
        if process is not None:
            process.terminate()
            process.wait()
            logger.debug("systemd-inhibit stopped")
