"""检查交付文件名称、来源清单、资源、文档链接与分发制品。"""

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

ROOT = Path(__file__).resolve().parents[1]
# 字符码规则避免检查配置自身带入禁用原文。
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
        f"{name}: 禁用名称规则 {index + 1} 命中"
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
                issues.append("抽离清单来源数量不一致")
        else:
            if manifest["sourceFileCount"] != len(manifest["sources"]):
                issues.append("历史来源数量不一致")
            source_ids = {row["sourceId"] for row in manifest["sources"]}
            for row in manifest[key]:
                if not set(row.get("sourceIds", [])) <= source_ids:
                    issues.append(f"未知历史来源引用: {row.get('target')}")
        seen = set()
        for row in manifest[key]:
            name = row.get("target")
            if name is None:
                if not row.get("excludedReason"):
                    issues.append(f"来源未分类: {row.get('source')}")
                continue
            path = root / name
            if (
                name in seen
                or Path(name).is_absolute()
                or ".." in Path(name).parts
                or not path.resolve().is_relative_to(root.resolve())
            ):
                issues.append(f"清单目标重复或越界: {name}")
                continue
            seen.add(name)
            if not path.is_file():
                issues.append(f"缺少目标: {name}")
            elif row.get("targetSha256") != digest(path.read_bytes()):
                issues.append(f"目标摘要不一致: {name}")
        for folder in ("src", "examples"):
            for path in (root / folder).rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    name = path.relative_to(root).as_posix()
                    if name not in seen:
                        issues.append(f"{filename}: 未登记文件: {name}")
    return issues


def links(root, paths):
    issues = []
    for path in paths:
        if path.suffix != ".md":
            continue
        # 围栏中的代码不是 Markdown 链接。
        text = re.sub(r"```.*?```", "", path.read_text(), flags=re.DOTALL)
        for link in re.findall(r"\]\(([^\s)]+)", text):
            parts = urlsplit(link.strip("<>"))
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                issues.append(f"{path.relative_to(root)}: 无效本地链接 {link}")
    return issues


def repository(root):
    paths = project_files(root)
    issues = []
    for path in paths:
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            issues.append(f"交付文件不可为符号链接: {name}")
        data = path.read_bytes()
        issues.extend(scan(name, data))
        if path.suffix == ".py":
            try:
                ast.parse(data, filename=name)
            except SyntaxError as error:
                issues.append(f"Python 语法错误: {name}: {error}")
    issues.extend(manifests(root))
    issues.extend(links(root, paths))
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    project = metadata["project"]
    if project["name"] != "openbacktesting" or project["version"] != "0.2.0":
        issues.append("发行身份或版本不一致")
    for name in RESOURCES:
        if not (root / "src/openbacktesting" / name).is_file():
            issues.append(f"运行资源缺失: {name}")
    return issues, len(paths)


def artifact(path):
    issues = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            members = {
                name: archive.read(name) for name in archive.namelist() if not name.endswith("/")
            }
        for resource in RESOURCES:
            if f"openbacktesting/{resource}" not in members:
                issues.append(f"{path.name}: wheel 缺少资源 {resource}")
        metadata = members.get("openbacktesting-0.2.0.dist-info/METADATA", b"")
        if b"Name: openbacktesting\n" not in metadata or b"Version: 0.2.0\n" not in metadata:
            issues.append(f"{path.name}: wheel 发行元数据不一致")
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            members = {}
            for member in archive:
                if member.issym() or member.islnk():
                    issues.append(f"{path.name}: 制品含链接 {member.name}")
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
            "tests/fixtures/portfolio.json",
            "examples/README.md",
            "docs/core/index.md",
            "tests/fixtures/engine-indicator-coverage-disposition.json",
        ]
        required += [f"src/openbacktesting/{name}" for name in RESOURCES]
        for name in required:
            if prefix + name not in members:
                issues.append(f"{path.name}: sdist 缺少文件 {name}")
    else:
        return [f"无法识别制品: {path}"], 0
    for name, data in members.items():
        issues.extend(scan(f"{path.name}/{name}", data))
        if Path(name).is_absolute() or ".." in Path(name).parts:
            issues.append(f"制品成员路径越界: {name}")
        if set(Path(name).parts) & LOCAL_OUTPUTS or Path(name).suffix in {".pyc", ".pyo"}:
            issues.append(f"制品包含本地缓存或构建输出: {name}")
    return issues, len(members)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, action="append", default=[])
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    issues, count = repository(args.root.resolve())
    for path in args.artifact:
        errors, members = artifact(path)
        issues.extend(errors)
        print(f"检查制品 {path.name}: {members} 文件")
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"完整性检查通过: {count} 项目文件，禁用名称零命中")


if __name__ == "__main__":
    main()
