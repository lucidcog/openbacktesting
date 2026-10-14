"""Versioned, atomic user presets; never rewrite strategy defaults."""

import os
import re
import secrets
from pathlib import Path

from openbacktesting_studio.protocol import DataProfile, Preset
from openbacktesting_studio.workspace import WorkspaceError


class ConfigurationStore:
    def __init__(self, root):
        self.root = Path(root)

    def directory(self, kind):
        if kind not in {"profiles", "presets"}:
            raise WorkspaceError("InvalidConfiguration", "Unknown configuration type", 422)
        path = self.root
        for part in [".openbacktesting", "studio", kind]:
            path /= part
            if path.is_symlink():
                raise WorkspaceError("PathDenied", "Configuration directory cannot be a link", 403)
            path.mkdir(exist_ok=True)
        return path

    def list(self, kind):
        directory = self.directory(kind)
        return [
            {"id": path.stem, "value": self.get(kind, path.stem)}
            for path in sorted(directory.glob("*.json"))
        ]

    def path(self, kind, name):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name):
            raise WorkspaceError(
                "InvalidConfiguration", "Use a simple configuration identifier", 422
            )
        path = self.directory(kind) / (name + ".json")
        if path.is_symlink():
            raise WorkspaceError("PathDenied", "Configuration cannot be a link", 403)
        return path

    def get(self, kind, name):
        path = self.path(kind, name)
        if not path.is_file():
            raise WorkspaceError("ConfigurationNotFound", "Configuration does not exist", 404)
        model = DataProfile if kind == "profiles" else Preset
        return model.model_validate_json(path.read_bytes()).model_dump()

    def put(self, kind, name, value):
        model = DataProfile if kind == "profiles" else Preset
        normalized = model.model_validate(value)
        path = self.path(kind, name)
        temporary = path.with_name("." + secrets.token_hex(16))
        try:
            with temporary.open("x") as stream:
                stream.write(normalized.model_dump_json(indent=2))
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return normalized.model_dump()
