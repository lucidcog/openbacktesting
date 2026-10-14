"""Regenerate Studio-owned JSON schemas without changing framework contracts."""

import json
from pathlib import Path

from openbacktesting_studio.protocol import SCHEMAS

root = Path(__file__).resolve().parents[1] / "src/openbacktesting_studio/protocol/schemas"
root.mkdir(parents=True, exist_ok=True)
for name, model in SCHEMAS.items():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **model.model_json_schema(),
    }
    (root / f"{name}.json").write_text(json.dumps(schema, indent=2) + "\n")
