from __future__ import annotations

import pathlib

import pytest

from zulup.util_pytest import TtestProjectDirectory


@pytest.fixture
def project(tmp_path: pathlib.Path) -> TtestProjectDirectory:
    return TtestProjectDirectory(tmp_path=tmp_path)
