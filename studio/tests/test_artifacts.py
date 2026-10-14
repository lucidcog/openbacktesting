import zipfile

import pytest

from openbacktesting_studio.artifacts import (
    export_container,
    import_container,
    validate,
    write_manifest,
)


def test_default_share_omits_source_raw_data_and_logs(tmp_path):
    result = tmp_path / "run"
    result.mkdir()
    for name in ["portfolio.json", "source/strategy.py", "data/array.npy", "logs.json"]:
        path = result / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("{}")
    write_manifest(result, run_id="a", provenance={"sourceHash": "known"})
    bundle = tmp_path / "share.obstudio"
    export_container(result, bundle)
    manifest = import_container(bundle, tmp_path / "import")
    assert [entry.path for entry in manifest.artifacts] == ["portfolio.json"]
    assert validate(tmp_path / "import").runId == "a"
    assert (result / "source/strategy.py").is_file()


@pytest.mark.parametrize("name", ["../escaped", "/absolute", "C:/drive", "a\\b"])
def test_unsafe_archive_paths_are_rejected(tmp_path, name):
    bundle = tmp_path / "bad.obstudio"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr(name, "unsafe")
    with pytest.raises(ValueError):
        import_container(bundle, tmp_path / "import")
    assert not (tmp_path / "import").exists()


def test_bad_checksum_and_expansion_limits(tmp_path):
    source = tmp_path / "run"
    source.mkdir()
    (source / "portfolio.json").write_text("{}")
    write_manifest(source, run_id="a", provenance={})
    bundle = tmp_path / "share.obstudio"
    export_container(source, bundle)
    with pytest.raises(ValueError, match="limits"):
        import_container(bundle, tmp_path / "import", max_bytes=1)
    (source / "portfolio.json").write_text("[]")
    with pytest.raises(ValueError, match="checksum"):
        validate(source)


@pytest.mark.parametrize("kind", ["duplicate", "link", "future", "feature"])
def test_untrusted_members_and_unknown_versions(tmp_path, kind):
    import json
    import stat

    source = tmp_path / "original"
    source.mkdir()
    (source / "portfolio.json").write_text("{}")
    write_manifest(source, run_id="safe", provenance={})
    target = tmp_path / "test.obstudio"
    export_container(source, target)
    with zipfile.ZipFile(target) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    if kind in {"future", "feature"}:
        manifest = json.loads(entries["manifest.json"])
        manifest["schemaVersion" if kind == "future" else "requiredFeatures"] = (
            2 if kind == "future" else ["future"]
        )
        entries["manifest.json"] = json.dumps(manifest).encode()
    with zipfile.ZipFile(target, "w") as archive:
        for name, value in entries.items():
            archive.writestr(name, value)
        if kind == "link":
            link = zipfile.ZipInfo("link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, "../outside")
        elif kind == "duplicate":
            with pytest.warns(UserWarning):
                archive.writestr("portfolio.json", "{}")
    with pytest.raises(ValueError):
        import_container(target, tmp_path / "result")
    assert not (tmp_path / "result").exists()


@pytest.mark.parametrize("mask", range(8))
def test_export_resource_options_include_exactly_selected_private_files(tmp_path, mask):
    result = tmp_path / "run"
    result.mkdir()
    public = {"portfolio.json", "plotting.json", "provenance.json"}
    source = {"source/strategy.py", "source/helpers.py"}
    data = {"data/bars.npy", "data/metadata.json"}
    logs = {"logs.json", "stdout.json", "stderr.json"}
    for name in public | source | data | logs:
        path = result / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("{}")
    write_manifest(result, run_id="qa", provenance={})
    bundle = tmp_path / "result.obstudio"
    export_container(
        result,
        bundle,
        include_source=bool(mask & 1),
        include_data=bool(mask & 2),
        include_logs=bool(mask & 4),
    )
    manifest = import_container(bundle, tmp_path / "import")
    expected = public | (source if mask & 1 else set()) | (data if mask & 2 else set())
    expected |= logs if mask & 4 else set()
    assert {entry.path for entry in manifest.artifacts} == expected
    assert {entry.path for entry in validate(result).artifacts} == public | source | data | logs
