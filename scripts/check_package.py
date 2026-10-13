"""Check deliverable names, provenance manifests, resources, documentation links, and artifacts."""

import argparse
import ast
import base64
import hashlib
import json
import re
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from check_language import REGISTRY, check_files

ROOT = Path(__file__).resolve().parents[1]
# Character-code rules keep forbidden names out of the checker configuration itself.
FORBIDDEN = tuple(
    bytes(codes)
    for codes in (
        (99, 97, 110, 100, 108, 101, 100, 111, 99, 107),
        (99, 97, 110, 100, 108, 101, 100, 111, 99, 107, 99, 111, 114, 101),
    )
)
LOCAL_OUTPUTS = {
    ".git",
    ".venv",
    ".verification",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "dist",
    "build",
    "htmlcov",
}
RESOURCES = (
    "py.typed",
    "indicators/catalog.json",
    "portfolio/catalog.json",
    "optimizer/portfolio-result.schema.json",
    "test/GOOG.csv",
    "test/BTCUSD.csv",
    "test/EURUSD.csv",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scan(name, data):
    haystack = name.encode().lower() + b"\n" + data.lower()
    if name.endswith(".json"):
        try:
            value = json.loads(data)
        except (ValueError, UnicodeDecodeError):
            value = None
        if isinstance(value, dict) and "pickle_base64" in value:
            haystack += b"\n" + base64.b64decode(value["pickle_base64"]).lower()
    return [
        f"{name}: forbidden-name rule {index + 1} matched"
        for index, term in enumerate(FORBIDDEN)
        if term in haystack
    ]


def project_files(root):
    if (root / ".git").exists():
        names = (
            subprocess.check_output(
                [
                    "git",
                    "--no-optional-locks",
                    "ls-files",
                    "-z",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                ],
                cwd=root,
            )
            .decode()
            .split("\0")
        )
        return sorted({root / name for name in names if name and (root / name).is_file()})
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and not set(p.relative_to(root).parts) & LOCAL_OUTPUTS
        and p.suffix not in {".pyc", ".pyo"}
    )


def manifests(root):
    issues = []
    for filename, key in (
        ("source-manifest.json", "targets"),
        ("extraction-manifest.json", "files"),
    ):
        manifest = json.loads((root / filename).read_text())
        if filename == "extraction-manifest.json":
            if manifest["sourceFileCount"] != len(manifest[key]):
                issues.append("Extraction manifest source count mismatch")
        else:
            if manifest["sourceFileCount"] != len(manifest["sources"]):
                issues.append("Historical source count mismatch")
            source_ids = {row["sourceId"] for row in manifest["sources"]}
            for row in manifest[key]:
                if not set(row.get("sourceIds", [])) <= source_ids:
                    issues.append(f"Unknown historical source reference: {row.get('target')}")
        seen = set()
        for row in manifest[key]:
            name = row.get("target")
            if name is None:
                if not row.get("excludedReason"):
                    issues.append(f"Unclassified source: {row.get('source')}")
                continue
            path = root / name
            if (
                name in seen
                or Path(name).is_absolute()
                or ".." in Path(name).parts
                or not path.resolve().is_relative_to(root.resolve())
            ):
                issues.append(f"Duplicate or out-of-bounds manifest target: {name}")
                continue
            seen.add(name)
            if not path.is_file():
                issues.append(f"Missing target: {name}")
            elif row.get("targetSha256") != digest(path.read_bytes()):
                issues.append(f"Target digest mismatch: {name}")
        for folder in ("src", "examples"):
            for path in (root / folder).rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    name = path.relative_to(root).as_posix()
                    if name not in seen:
                        issues.append(f"{filename}: unregistered file: {name}")
    return issues


def links(root, paths):
    issues = []
    for path in paths:
        if path.suffix != ".md":
            continue
        # Code inside fences is not a Markdown link.
        text = re.sub(r"```.*?```", "", path.read_text(), flags=re.DOTALL)
        for link in re.findall(r"\]\(([^\s)]+)", text):
            parts = urlsplit(link.strip("<>"))
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                issues.append(f"{path.relative_to(root)}: invalid local link {link}")
    return issues


def repository(root):
    paths = project_files(root)
    issues = []
    for path in paths:
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            issues.append(f"Deliverable must not be a symbolic link: {name}")
        data = path.read_bytes()
        issues.extend(scan(name, data))
        if path.suffix == ".py":
            try:
                ast.parse(data, filename=name)
            except SyntaxError as error:
                issues.append(f"Python syntax error: {name}: {error}")
    issues.extend(manifests(root))
    issues.extend(links(root, paths))
    issues.extend(
        check_files({path.relative_to(root).as_posix(): path.read_bytes() for path in paths})
    )
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    project = metadata["project"]
    if project["name"] != "openbacktesting" or project["version"] != "0.2.0":
        issues.append("Distribution identity or version mismatch")
    for name in RESOURCES:
        if not (root / "src/openbacktesting" / name).is_file():
            issues.append(f"Missing runtime resource: {name}")
    return issues, len(paths)


def artifact(path, registry_data=None):
    issues = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            members = {
                name: archive.read(name) for name in archive.namelist() if not name.endswith("/")
            }
        for resource in RESOURCES:
            if f"openbacktesting/{resource}" not in members:
                issues.append(f"{path.name}: wheel is missing resource {resource}")
        metadata = members.get("openbacktesting-0.2.0.dist-info/METADATA", b"")
        if b"Name: openbacktesting\n" not in metadata or b"Version: 0.2.0\n" not in metadata:
            issues.append(f"{path.name}: wheel distribution metadata mismatch")
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            members = {}
            for member in archive:
                if member.issym() or member.islnk():
                    issues.append(f"{path.name}: artifact contains a link {member.name}")
                if member.isfile():
                    members[member.name] = archive.extractfile(member).read()
        prefix = "openbacktesting-0.2.0/"
        required = [
            "pyproject.toml",
            "uv.lock",
            "README.md",
            "conftest.py",
            "source-manifest.json",
            "extraction-manifest.json",
            "scripts/check_package.py",
            "scripts/check_language.py",
            REGISTRY,
            "tests/fixtures/portfolio.json",
            "examples/README.md",
            "docs/core/index.md",
            "tests/fixtures/engine-indicator-coverage-disposition.json",
        ]
        required += [f"src/openbacktesting/{name}" for name in RESOURCES]
        for name in required:
            if prefix + name not in members:
                issues.append(f"{path.name}: sdist is missing file {name}")
    else:
        return [f"Unrecognized artifact: {path}"], 0
    for name, data in members.items():
        issues.extend(scan(f"{path.name}/{name}", data))
        if Path(name).is_absolute() or ".." in Path(name).parts:
            issues.append(f"Artifact member path escapes its root: {name}")
        if set(Path(name).parts) & LOCAL_OUTPUTS or Path(name).suffix in {".pyc", ".pyo"}:
            issues.append(f"Artifact contains local cache or build output: {name}")
    normalized = {}
    for name, data in members.items():
        if name.startswith("openbacktesting-0.2.0/"):
            name = name.removeprefix("openbacktesting-0.2.0/")
        elif name.startswith("openbacktesting/"):
            name = "src/" + name
        normalized[name] = data
    if REGISTRY in normalized:
        registry_data = normalized[REGISTRY]
    if registry_data is None:
        registry_path = ROOT / REGISTRY
        registry_data = registry_path.read_bytes() if registry_path.is_file() else None
    # Hatch embeds README.md in both metadata formats. Apply the same exact
    # localization exceptions to each copy while still checking all headers.
    for name in ("openbacktesting-0.2.0.dist-info/METADATA", "PKG-INFO"):
        headers, separator, description = normalized.get(name, b"").partition(b"\n\n")
        if separator and b"Description-Content-Type: text/markdown" in headers.splitlines():
            normalized[name] = headers
            issues.extend(
                f"{name}: {issue}"
                for issue in check_files({"README.md": description}, registry_data, subset=True)
            )
    issues.extend(check_files(normalized, registry_data, subset=True))
    return issues, len(members)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, action="append", default=[])
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    issues, count = repository(args.root.resolve())
    registry_path = args.root.resolve() / REGISTRY
    registry_data = registry_path.read_bytes() if registry_path.is_file() else None
    for path in args.artifact:
        errors, members = artifact(path, registry_data)
        issues.extend(errors)
        print(f"Checked artifact {path.name}: {members} files")
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"Integrity check passed: {count} project files; no forbidden names found")


if __name__ == "__main__":
    main()
