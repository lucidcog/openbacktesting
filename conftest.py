"""Isolate test and tutorial file side effects in the pytest temporary directory."""

import pytest


@pytest.fixture(autouse=True)
def isolated_output_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
