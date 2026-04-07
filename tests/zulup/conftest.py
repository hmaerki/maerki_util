from __future__ import annotations

import pathlib

import pytest

from zulup.util_pytest import TestProjectDirectory


@pytest.fixture
def project(tmp_path: pathlib.Path) -> TestProjectDirectory:
    return TestProjectDirectory(tmp_path=tmp_path)
