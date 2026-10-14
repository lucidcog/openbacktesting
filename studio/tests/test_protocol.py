import json

import pytest
from pydantic import ValidationError

from openbacktesting_studio.protocol import DataProfile, Preset, RunManifest, relative_path


def profile():
    return {
        "name": "Daily example",
        "kind": "sample",
        "sample": "GOOG",
        "timezone": "UTC",
        "timeframe": {"unit": "day", "multiplier": 1},
        "instrument": {"symbol": "GOOG"},
    }


def test_profile_roundtrip_and_explicit_units():
    value = DataProfile.model_validate(profile())
    assert DataProfile.model_validate_json(value.model_dump_json()) == value
    for change in (
        {"schemaVersion": True},
        {"schemaVersion": 2},
        {"timezone": "invalid"},
        {"timeframe": {"unit": "day", "multiplier": True}},
        {"kind": "csv", "sample": None},
        {"unknown": 1},
        {"instrument": {"symbol": "GOOG", "price_tick": float("inf")}},
    ):
        with pytest.raises(ValidationError):
            DataProfile.model_validate(profile() | change)


@pytest.mark.parametrize("path", ["../a", "/a", "a/../b", "a\\b", "a//b", "C:/a", "a\x00"])
def test_wire_paths_reject_ambiguous_or_external_paths(path):
    with pytest.raises(ValueError):
        relative_path(path)


def test_preset_preserves_core_schema_and_title_values():
    data = {
        "name": "Conservative",
        "inputs": {
            "schemaVersion": "1.0.0",
            "schemaHash": "core-owned-hash",
            "values": {"Quantity": 1, "Enabled": False},
        },
    }
    saved = json.loads(Preset.model_validate(data).model_dump_json())
    assert saved["schemaVersion"] == 1
    assert saved["inputs"] == data["inputs"]


def test_manifest_rejects_future_features_and_duplicate_members():
    base = {"runId": "run-1", "status": "succeeded", "provenance": {}, "artifacts": []}
    assert RunManifest.model_validate(base).schemaVersion == 1
    entry = {"path": "portfolio.json", "sha256": "a" * 64, "size": 0}
    for update in (
        {"requiredFeatures": ["future"]},
        {"artifacts": [entry, entry]},
        {"schemaVersion": 2},
        {"runId": "../escape"},
    ):
        with pytest.raises(ValidationError):
            RunManifest.model_validate(base | update)
