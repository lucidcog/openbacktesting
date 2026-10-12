"""将测试与教程的文件副作用隔离在 pytest 临时目录。"""

import pytest


@pytest.fixture(autouse=True)
def isolated_output_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
