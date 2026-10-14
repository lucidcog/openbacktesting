from pathlib import Path
from types import SimpleNamespace

import pytest

from openbacktesting_studio.cli import main


def test_no_open_and_readonly_keep_original_unchanged(tmp_path, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr("webbrowser.open", lambda url: pytest.fail("Browser must not open"))
    monkeypatch.setattr(
        "uvicorn.Server",
        lambda config: SimpleNamespace(run=lambda sockets: calls.append(config.app)),
    )
    main([str(tmp_path), "--no-open", "--port", "0"])
    assert calls[-1].state.workspace is None
    assert calls[-1].state.suggested_workspace == str(tmp_path)
    output = capsys.readouterr().out
    assert "http://127.0.0.1:" in output and "#token=" in output
    original = Path(__file__).parent / "fixtures/portfolio.json"
    before = original.read_bytes()
    main(["view", str(original), "--no-open", "--python", "/does/not/exist", "--port", "0"])
    assert calls[-1].state.workspace is None
    assert original.read_bytes() == before


@pytest.mark.parametrize("arguments", [["view"], ["a", "b"], ["--port", "bad"]])
def test_invalid_cli_arguments_exit_nonzero(arguments):
    with pytest.raises(SystemExit) as failure:
        main(arguments)
    assert failure.value.code == 2
