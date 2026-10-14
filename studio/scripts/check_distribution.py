"""Check the installed-resource boundary of Studio wheels and source distributions."""

import argparse
import email
import tarfile
import zipfile
from pathlib import Path


def check(path):
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            files = {
                name: archive.read(name) for name in archive.namelist() if not name.endswith("/")
            }
        prefix = "openbacktesting_studio/"
        metadata_name = next(name for name in files if name.endswith(".dist-info/METADATA"))
    else:
        with tarfile.open(path) as archive:
            if any(item.issym() or item.islnk() for item in archive.getmembers()):
                raise ValueError("Distribution contains links")
            files = {
                item.name.split("/", 1)[1]: archive.extractfile(item).read()
                for item in archive.getmembers()
                if item.isfile()
            }
        prefix = "src/openbacktesting_studio/"
        metadata_name = "PKG-INFO"
    metadata = email.message_from_bytes(files[metadata_name])
    assert metadata["Name"] == "openbacktesting-studio"
    assert any(
        dep.startswith(("openbacktesting<", "openbacktesting>="))
        for dep in metadata.get_all("Requires-Dist", [])
    )
    for resource in [
        "__init__.py",
        "web/index.html",
        "web/chart-provenance.json",
        "web/lightweight-charts-LICENSE.txt",
        "web/lightweight-charts-NOTICE.txt",
    ]:
        assert prefix + resource in files, resource
    for name in files:
        assert not {"node_modules", "vendor", "__pycache__", "openbacktesting"} & set(
            Path(name).parts
        ), name
        assert ".." not in Path(name).parts and not Path(name).is_absolute(), name
    print(f"{path.name}: verified {len(files)} members, {path.stat().st_size} compressed bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+")
    for path in parser.parse_args().paths:
        check(path)
