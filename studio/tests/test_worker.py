import sys

import pytest

from openbacktesting_studio.execution.process import discover, probe
from openbacktesting_studio.protocol import SourceRequest
from openbacktesting_studio.workspace import Workspace, WorkspaceError

SOURCE = """from openbacktesting import Strategy, backtest, inputs
@backtest()
class Example(Strategy):
    length = inputs.int(10, title="Length")
    def init(self):
        raise RuntimeError("Discovery must not run init")
    def next(self):
        pass
"""


def capture(tmp_path, text):
    (tmp_path / "strategy.py").write_text(text)
    workspace = Workspace(tmp_path)
    return workspace.capture(
        SourceRequest(path="strategy.py", revision=workspace.read("strategy.py")["revision"])
    )


def test_probe_and_fresh_discovery(tmp_path):
    assert probe(sys.executable)["compatible"]
    assert not probe("/missing/python")["compatible"]
    snapshot = capture(tmp_path, 'print("user output")\n' + SOURCE)
    result = discover(sys.executable, snapshot)
    assert result["ok"] and result["description"]["schemaHash"]
    assert result["stdout"]["text"] == "user output\n"
    assert result["sourceHash"] == snapshot["hash"]
    changed = capture(tmp_path, SOURCE.replace("Length", "New length"))
    assert (
        discover(sys.executable, changed)["description"]["schemaHash"]
        != result["description"]["schemaHash"]
    )


@pytest.mark.parametrize(
    "core_version, compatible",
    [("0.2.0", False), ("0.2.1", True), ("0.2.2", True), ("0.3.0", False)],
)
def test_probe_requires_core_serialization_fix(monkeypatch, core_version, compatible):
    import json
    import subprocess

    from openbacktesting_studio import __version__

    info = {
        "protocolVersion": 1, "coreVersion": core_version,
        "studioVersion": __version__, "pythonVersion": "3.12.0",
    }
    monkeypatch.setattr(
        subprocess, "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, json.dumps(info)),
    )
    assert probe(sys.executable)["compatible"] is compatible


@pytest.mark.parametrize(
    "text", ["broken syntax ???", "import missing_studio_test_dependency", "value = 1"]
)
def test_discovery_errors_have_diagnostics(tmp_path, text):
    with pytest.raises(WorkspaceError) as error:
        discover(sys.executable, capture(tmp_path, text))
    assert error.value.code == "DiscoveryFailed"
    assert error.value.details["frames"]


def test_hung_import_is_terminated(tmp_path):
    with pytest.raises(WorkspaceError) as error:
        discover(sys.executable, capture(tmp_path, "while True: pass"), timeout=0.5)
    assert error.value.code == "WorkerTimeout"


def test_output_is_bounded_and_version_mismatch_is_explicit(tmp_path, monkeypatch):
    import json
    import subprocess

    from openbacktesting_studio.execution.process import ManagedProcess

    process = ManagedProcess(
        [
            sys.executable,
            "-c",
            'import sys; sys.stdout.write("x" * 3000000); sys.stderr.write("y" * 3000000)',
        ]
    )
    assert process.wait(10) == 0
    for tail in [process.stdout, process.stderr]:
        value = tail.export()
        assert value["truncated"] and len(value["text"]) <= 1048576
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args, 0, json.dumps({"protocolVersion": 99, "coreVersion": "0.2.0"})
        ),
    )
    result = probe(sys.executable)
    assert not result["compatible"] and "incompatible" in result["message"]


def test_duplicate_entries_and_error_source_revision(tmp_path):
    from hashlib import sha256

    source = SOURCE + SOURCE.replace("class Example", "class Other")
    with pytest.raises(WorkspaceError, match="exactly one"):
        discover(sys.executable, capture(tmp_path, source))
    broken = 'raise RuntimeError("frozen error")\n'
    snapshot = capture(tmp_path, broken)
    (tmp_path / "strategy.py").write_text('current = "different"\n')
    with pytest.raises(WorkspaceError) as failure:
        discover(sys.executable, snapshot)
    frame = next(
        frame
        for frame in failure.value.details["frames"]
        if frame.get("workspacePath") == "strategy.py"
    )
    assert frame["sourceRevision"] == sha256(broken.encode()).hexdigest()
    assert frame["snapshot"] is True


def test_collected_logs_preserve_messages_and_map_only_captured_source(tmp_path):
    from openbacktesting_studio.execution.worker import collected_logs

    rows = [
        {"source_file": str(tmp_path / "strategy.py"), "source_line": 12, "message": "line\ntext"},
        {"source_file": "/external/library.py", "source_line": 1, "message": "external"},
    ]

    class Logs:
        def get_logs(self):
            return [dict(row) for row in rows]

    value = collected_logs(
        Logs(), snapshot={"directory": str(tmp_path), "files": {"strategy.py": "revision"}}
    )
    assert value["records"][0]["source"] == {
        "workspacePath": "strategy.py",
        "line": 12,
        "sourceRevision": "revision",
    }
    assert value["records"][0]["message"] == "line\ntext"
    assert "source" not in value["records"][1]
    assert "source" not in rows[0]
    assert collected_logs(Logs(), limit=1)["truncated"]
