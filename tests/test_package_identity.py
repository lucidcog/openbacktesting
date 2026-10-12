"""更名后的独立发行、资源及序列化边界。"""

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
    # wheel 只公开唯一包根；editable 安装通过公开对象元数据验证。
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
