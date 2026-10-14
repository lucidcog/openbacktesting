import os
from pathlib import Path

import pytest

from openbacktesting_studio.protocol import SourceRequest
from openbacktesting_studio.workspace import Workspace, WorkspaceError


def test_saved_bytes_permissions_conflict_and_deleted_file(tmp_path):
    path = tmp_path / "strategy.py"
    path.write_bytes(b"# example\r\nvalue = 1\r\n")
    path.chmod(0o640)
    workspace = Workspace(tmp_path)
    original = workspace.read("strategy.py")
    saved = workspace.save(
        "strategy.py", original["revision"], original["content"].replace("1", "2")
    )
    assert path.read_bytes() == b"# example\r\nvalue = 2\r\n"
    assert path.stat().st_mode & 0o777 == 0o640
    path.write_text("external = 3")
    with pytest.raises(WorkspaceError, match="changed on disk"):
        workspace.save("strategy.py", saved["revision"], "draft = 4")
    assert path.read_text() == "external = 3"
    path.unlink()
    with pytest.raises(WorkspaceError) as error:
        workspace.save("strategy.py", saved["revision"], "draft = 4")
    assert error.value.status == 404 and not path.exists()


def test_paths_encoding_limits_and_nonregular_files(tmp_path):
    workspace = Workspace(tmp_path, max_file_bytes=4)
    (tmp_path / "link.py").symlink_to("/etc/passwd")
    (tmp_path / "binary.py").write_bytes(b"\x00")
    (tmp_path / "large.py").write_text("large")
    os.mkfifo(tmp_path / "pipe.py")
    for name in [
        "../outside.py",
        "/etc/passwd",
        "link.py",
        "binary.py",
        "large.py",
        "pipe.py",
        ".openbacktesting/state.py",
    ]:
        with pytest.raises(WorkspaceError):
            workspace.read(name)


def test_snapshot_preserves_dynamic_modules_and_freezes_resources(tmp_path):
    (tmp_path / "strategy.py").write_text('import importlib\nimportlib.import_module("helper")')
    (tmp_path / "helper.py").write_text("value = 1")
    (tmp_path / "data.csv").write_text("Close\n1")
    workspace = Workspace(tmp_path)
    request = SourceRequest(path="strategy.py", revision=workspace.read("strategy.py")["revision"])
    snapshot = workspace.capture(request, ["data.csv"])
    (tmp_path / "helper.py").write_text("value = 2")
    root = Path(snapshot["directory"])
    assert (root / "helper.py").read_text() == "value = 1"
    assert (root / "data.csv").read_text() == "Close\n1"
    assert not (root / ".openbacktesting").exists()
    assert all(not name.startswith(".openbacktesting") for name in workspace.list())


def test_snapshot_detects_mutation_during_read(tmp_path, monkeypatch):
    (tmp_path / "strategy.py").write_text("value = 1")
    workspace = Workspace(tmp_path)
    request = SourceRequest(path="strategy.py", revision=workspace.read("strategy.py")["revision"])
    original = workspace.read_bytes
    calls = 0

    def mutate(name, **kwargs):
        nonlocal calls
        calls += 1
        value = original(name, **kwargs)
        if calls == 1:
            (tmp_path / "strategy.py").write_text("value = 2")
        return value

    monkeypatch.setattr(workspace, "read_bytes", mutate)
    with pytest.raises(WorkspaceError, match="during capture"):
        workspace.capture(request)
