"""Immutable, checksummed data containers; never deserialize executable objects."""

import json
import shutil
import stat
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path

from openbacktesting_studio.protocol import RunManifest, relative_path

MAX_BYTES = 512 * 1024 * 1024
MAX_ENTRIES = 20000


def strict_json(data):
    def reject(value):
        raise ValueError(f"Non-finite JSON value: {value}")

    def unique(pairs):
        output = {}
        for key, value in pairs:
            if key in output:
                raise ValueError(f"Duplicate JSON key: {key}")
            output[key] = value
        return output

    return json.loads(data, parse_constant=reject, object_pairs_hook=unique)


def validate(directory):
    directory = Path(directory)
    manifest = RunManifest.model_validate(strict_json((directory / "manifest.json").read_bytes()))
    for entry in manifest.artifacts:
        path = directory / entry.path
        if any(
            parent.is_symlink()
            for parent in [path, *path.parents]
            if parent.is_relative_to(directory)
        ):
            raise ValueError("Linked artifact is not allowed")
        if not path.is_file() or path.stat().st_size != entry.size:
            raise ValueError(f"Missing or truncated artifact: {entry.path}")
        if sha256(path.read_bytes()).hexdigest() != entry.sha256:
            raise ValueError(f"Artifact checksum mismatch: {entry.path}")
    return manifest


def write_manifest(directory, *, run_id, provenance, diagnostics=()):
    directory = Path(directory)
    artifacts = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path != directory / "manifest.json":
            data = path.read_bytes()
            artifacts.append(
                {
                    "path": path.relative_to(directory).as_posix(),
                    "size": len(data),
                    "sha256": sha256(data).hexdigest(),
                }
            )
    manifest = RunManifest(
        runId=run_id,
        status="succeeded",
        provenance=provenance,
        diagnostics=list(diagnostics),
        artifacts=artifacts,
    )
    temporary = directory / "manifest.tmp"
    temporary.write_text(manifest.model_dump_json(indent=2))
    temporary.replace(directory / "manifest.json")
    return manifest


def export_container(
    directory, target, *, include_source=False, include_data=False, include_logs=False
):
    directory = Path(directory)
    manifest = validate(directory)

    def selected(name):
        if name.startswith("source/"):
            return include_source
        if name.startswith("data/"):
            return include_data
        if name in {"logs.json", "stdout.json", "stderr.json"}:
            return include_logs
        return True

    manifest.artifacts = [entry for entry in manifest.artifacts if selected(entry.path)]
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest.model_dump_json())
        for entry in manifest.artifacts:
            archive.write(directory / entry.path, entry.path)
    return manifest


def import_container(source, destination, *, max_bytes=MAX_BYTES):
    destination = Path(destination)
    temporary = Path(tempfile.mkdtemp(dir=destination.parent))
    try:
        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) > MAX_ENTRIES or len(set(names)) != len(names):
                raise ValueError("Too many or duplicate archive entries")
            total = 0
            for entry in entries:
                name = relative_path(entry.filename)
                if Path(name).suffix.lower() in {".pkl", ".pickle"}:
                    raise ValueError("Executable serialization formats are not supported")
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                    raise ValueError("Only ordinary artifact entries are allowed")
                total += entry.file_size
                if (
                    total > max_bytes
                    or entry.file_size > max_bytes
                    or entry.file_size > max(1, entry.compress_size) * 1000
                ):
                    raise ValueError("Archive exceeds expansion limits")
                path = temporary / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as src, path.open("wb") as dst:
                    count = 0
                    while chunk := src.read(65536):
                        count += len(chunk)
                        if count > entry.file_size:
                            raise ValueError("Archive member exceeds declared size")
                        dst.write(chunk)
            manifest = validate(temporary)
            listed = {entry.path for entry in manifest.artifacts} | {"manifest.json"}
            if listed != set(names):
                raise ValueError("Archive members do not match manifest")
        if destination.exists():
            raise ValueError("Import destination already exists")
        temporary.replace(destination)
        return manifest
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def validate_portfolio(payload):
    from importlib.resources import files

    from jsonschema import Draft202012Validator

    schema = strict_json(
        files("openbacktesting").joinpath("optimizer/portfolio-result.schema.json").read_bytes()
    )
    Draft202012Validator(schema).validate(payload)
    return payload


def import_portfolio(source, destination):
    """Read core exports without executing any source or serialized Python objects."""
    payload = strict_json(Path(source).read_bytes())
    if not isinstance(payload, dict):
        raise TypeError("Import a JSON report object or an .obstudio archive")
    portfolio = payload.get("portfolio", payload)
    validate_portfolio(portfolio)
    plotting = payload.get("plotting")
    if plotting is not None:
        if plotting.get("schemaVersion") not in {"1.0.0", "1.1.0"}:
            raise ValueError("Unsupported plotting version")
        portfolio_fills = portfolio["facts"]["fills"]
        plot_fills = plotting["tradingFacts"]["fills"]
        keys = ("fill_id", "bar_index", "qty", "price", "side", "fee")
        if [[row[key] for key in keys] for row in portfolio_fills] != [
            [row[key] for key in keys] for row in plot_fills
        ]:
            raise ValueError("Portfolio and plotting fills do not match")
        bars = next(axis for axis in plotting["axes"] if axis["id"] == plotting["market"]["axis"])
        expected_kind = {"aware": "utc-ns", "naive": "naive-datetime", "ordinal": "ordinal"}.get(
            portfolio["context"]["timeKind"]
        )
        if (
            bars["kind"] != expected_kind
            or bars.get("timezone") != portfolio["context"]["timezone"]
        ):
            raise ValueError("Portfolio and plotting axis context does not match")
        labels = bars["labels"]
        if expected_kind == "naive-datetime":
            import pandas as pd

            # Plotting uses local ISO labels; Portfolio uses nanosecond integers.
            timestamps = [pd.Timestamp(label) for label in labels]
            if any(pd.isna(value) or value.tzinfo is not None for value in timestamps):
                raise ValueError("Invalid naive plotting timestamp")
            labels = [str(value.value) for value in timestamps]
        for row in portfolio["series"]["close"]:
            index = row["barIndex"]
            if index >= len(labels) or labels[index] != row["timestamp"]["value"]:
                raise ValueError("Portfolio and plotting bar identities do not match")
    destination = Path(destination)
    destination.mkdir(exist_ok=False)
    (destination / "portfolio.json").write_text(json.dumps(portfolio, allow_nan=False))
    if plotting is not None:
        (destination / "plotting.json").write_text(json.dumps(plotting, allow_nan=False))
    import uuid

    return write_manifest(
        destination,
        run_id=uuid.uuid4().hex,
        provenance={
            "imported": True,
            "pairing": "unverified-source" if plotting else "report-only",
            "reproducible": False,
        },
    )
