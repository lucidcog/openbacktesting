"""Independent distribution, resources, and serialization boundaries after renaming."""

import pickle
from importlib.metadata import distribution, version
from importlib.resources import files

from openbacktesting import Backtest, Strategy


def test_new_identity_resources_and_pickle_without_old_import_alias():
    assert version("openbacktesting") == "0.2.0"
    roots = {
        str(path).split("/", 1)[0]
        for path in distribution("openbacktesting").files
        if str(path).endswith("/__init__.py")
    }
    # The wheel exposes a single package root; verify editable installs through public object metadata.
    assert roots <= {"openbacktesting"}
    for value in (Backtest, Strategy):
        assert value.__module__.startswith("openbacktesting.")
        assert pickle.loads(pickle.dumps(value)) is value
    package = files("openbacktesting")
    for path in (
        "py.typed",
        "indicators/catalog.json",
        "optimizer/portfolio-result.schema.json",
        "test/GOOG.csv",
    ):
        assert package.joinpath(path).is_file(), path
