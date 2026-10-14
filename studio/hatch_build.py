"""Refuse missing, stale or mutated static resources; end-user builds need no Node."""

import json
from hashlib import sha256
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        web = root / "src/openbacktesting_studio/web"
        manifest = web / "build-manifest.json"
        if not manifest.is_file():
            raise ValueError("Build Studio web assets first: npm --prefix web run build")
        metadata = json.loads(manifest.read_text())
        for name, digest in metadata["assets"].items():
            path = web / name
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Stale or missing static asset: {name}")
        # The sdist intentionally ships prebuilt assets without a Node development tree.
        if (root / "web/src").is_dir():
            actual = {
                path.relative_to(root).as_posix()
                for path in (root / "web/src").rglob("*")
                if path.is_file()
            }
            expected = {name for name in metadata["inputs"] if name.startswith("web/src/")}
            if actual != expected:
                raise ValueError("Frontend source inventory changed; rebuild Studio web")
            for name, digest in metadata["inputs"].items():
                if sha256((root / name).read_bytes()).hexdigest() != digest:
                    raise ValueError(
                        f"Web source changed since the build: {name}; rebuild Studio web"
                    )
