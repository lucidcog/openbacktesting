import json
from pathlib import Path

import pytest
from test_data import profile

from openbacktesting_studio.workspace import WorkspaceError
from openbacktesting_studio.workspace.configuration import ConfigurationStore


def test_preset_and_profile_atomic_roundtrip_without_rewriting_source(tmp_path):
    source = tmp_path / "strategy.py"
    source.write_text("default = 10\n")
    store = ConfigurationStore(tmp_path)
    description = json.loads((Path(__file__).parent / "fixtures/inputs.json").read_text())
    preset = {
        "schemaVersion": 1,
        "name": "First",
        "inputs": {
            "schemaVersion": description["schemaVersion"],
            "schemaHash": description["schemaHash"],
            "values": {"Moving-average period": 30},
        },
        "settings": {},
    }
    assert store.put("presets", "first", preset) == preset
    assert store.list("presets")[0]["value"] == preset
    assert store.put("profiles", "sample", profile().model_dump()) == profile().model_dump()
    assert source.read_text() == "default = 10\n"
    assert not list((tmp_path / ".openbacktesting/studio/presets").glob(".*"))
    with pytest.raises(WorkspaceError):
        store.get("presets", "../escape")
    with pytest.raises(ValueError):
        store.put("presets", "future", preset | {"schemaVersion": 2})
