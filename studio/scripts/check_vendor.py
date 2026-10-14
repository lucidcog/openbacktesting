"""Verify the complete imported tree and every declared local modification."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "studio/vendor-metadata/lightweight-charts.json"


def verify():
    manifest = json.loads(MANIFEST.read_text())
    root = ROOT / manifest["root"]
    changes = {row["path"]: row for row in manifest["modifications"]}
    issues = []
    original = {row["path"]: row for row in manifest["files"]}
    for name, row in original.items():
        path = root / name
        if not path.is_file() or path.is_symlink():
            issues.append(f"Missing or linked upstream file: {name}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = changes.get(name, row).get("sha256")
        if actual != expected:
            issues.append(f"Unrecorded modification: {name}")
    for name, row in changes.items():
        if not row.get("reason") or name not in original:
            issues.append(f"Invalid modification record: {name}")
    discovered = (
        subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "."],
            cwd=root,
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .split("\0")
    )
    for name in filter(None, discovered):
        if name not in original and name not in changes:
            issues.append(f"Unrecorded added file: {name}")
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"Verified {len(original)} upstream files and {len(changes)} local modifications")


if __name__ == "__main__":
    verify()
