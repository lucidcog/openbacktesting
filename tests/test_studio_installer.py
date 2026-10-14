"""Exercise installer transactions without network access or changing user tools."""

import hashlib
import os
import shlex
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install-studio.sh"


def executable(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o755)


@pytest.fixture
def installation(tmp_path):
    source = tmp_path / "source checkout"
    for name in (
        "pyproject.toml", "README.md", "LICENSE", "src/example.py",
        "examples/strategies/ema_inputs.py", "studio/pyproject.toml", "studio/README.md",
        "studio/LICENSE", "studio/hatch_build.py", "studio/src/example.py",
        "studio/web/package.json", "studio/vendor/example.txt", "studio/vendor-metadata/example.json",
        "studio/tests/fixtures/portfolio.json",
    ):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original\n")
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    executable(fixtures / "node/bin/npm", """#!/bin/bash
printf '%s\\n' "$*" >> "$INSTALL_TEST_LOG"
[ -f "$2/../tests/fixtures/portfolio.json" ] || exit 9
if [ "${INSTALL_TEST_FAIL:-}" = build ] && [ "$4" = build ]; then exit 7; fi
""")
    archive = fixtures / "node-v22.23.3-darwin-arm64.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        stream.add(fixtures / "node", arcname="node")
    (fixtures / "SHASUMS256.txt").write_text(
        f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n"
    )
    executable(fixtures / "python", f"""#!/bin/bash
if [ "$1" = - ]; then exec {shlex.quote(sys.executable)} "$@"; fi
printf '%s\\n' "$0" >> "$INSTALL_TEST_LOG"
printf '%s\\n' "$*" >> "$INSTALL_TEST_LOG"
""")
    executable(fixtures / "uv", """#!/bin/bash
if [ "$1" = venv ]; then
    mkdir -p "$4/bin"
    cp "$INSTALL_TEST_FIXTURES/python" "$4/bin/python"
elif [ "${INSTALL_TEST_FAIL:-}" = install ]; then
    exit 8
fi
""")
    (fixtures / "uv-install.sh").write_text("""#!/bin/sh
mkdir -p "$UV_UNMANAGED_INSTALL"
cp "$INSTALL_TEST_FIXTURES/uv" "$UV_UNMANAGED_INSTALL/uv"
""")
    commands = tmp_path / "commands"
    executable(commands / "uname", """#!/bin/sh
if [ "$1" = -s ]; then echo "${INSTALL_TEST_OS:-Darwin}"; else echo arm64; fi
""")
    executable(commands / "id", "#!/bin/sh\necho 501\n")
    executable(commands / "curl", """#!/bin/bash
if [ "${INSTALL_TEST_FAIL:-}" = download ]; then exit 22; fi
while [ "$#" -gt 0 ]; do
    case "$1" in
        https://*) url=$1; shift ;;
        -o) output=$2; shift 2 ;;
        *) shift ;;
    esac
done
case "$url" in
    */uv/install.sh) cp "$INSTALL_TEST_FIXTURES/uv-install.sh" "$output" ;;
    */SHASUMS256.txt) cp "$INSTALL_TEST_FIXTURES/SHASUMS256.txt" "$output" ;;
    */node-*.tar.gz) cp "$INSTALL_TEST_FIXTURES/${url##*/}" "$output" ;;
    *) exit 23 ;;
esac
""")
    prefix = tmp_path / "installed studio"
    bin_dir = tmp_path / "user bin"
    log = tmp_path / "commands.log"
    env = dict(os.environ, PATH=f"{commands}:{os.environ['PATH']}",
               INSTALL_TEST_FIXTURES=str(fixtures), INSTALL_TEST_LOG=str(log))
    args = ["bash", str(INSTALLER), "--source", str(source), "--prefix", str(prefix),
            "--bin-dir", str(bin_dir), "--no-shortcut", "--no-launch"]

    def run(*extra, **overrides):
        return subprocess.run(args + list(extra), env={**env, **overrides}, text=True,
                              capture_output=True, timeout=30, check=False)

    return run, prefix, bin_dir, source, log, fixtures


def test_install_update_preserves_user_files_and_launcher_arguments(installation):
    run, prefix, bin_dir, source, log, _ = installation
    result = run()
    assert result.returncode == 0, result.stdout + result.stderr
    previous = (prefix / "current").resolve()
    example = prefix / "examples/ema_inputs.py"
    example.write_text("user edits\n")
    history = prefix / "examples/.openbacktesting/studio/history"
    history.parent.mkdir(parents=True)
    history.write_text("saved runs\n")
    result = run()
    assert result.returncode == 0, result.stdout + result.stderr
    assert previous.is_dir() and (prefix / "current").resolve() != previous
    assert example.read_text() == "user edits\n" and history.read_text() == "saved runs\n"
    assert (source / "examples/strategies/ema_inputs.py").read_text() == "original\n"
    command = bin_dir / "openbacktesting-studio"
    env = dict(os.environ, INSTALL_TEST_LOG=str(log))
    subprocess.run([str(command)], env=env, check=True)
    assert f"-m openbacktesting_studio.cli {prefix}/examples" in log.read_text()
    assert f"{(prefix / 'current').resolve()}/venv/bin/python" in log.read_text()
    subprocess.run([str(command), "view", "/tmp/result with spaces.obstudio", "--no-open"],
                   env=env, check=True)
    assert "view /tmp/result with spaces.obstudio --no-open" in log.read_text()
    assert not (prefix / ".install-lock").exists()


@pytest.mark.parametrize("failure", ["download", "build", "install", "checksum"])
def test_failed_update_keeps_previous_version(installation, failure):
    run, prefix, _, _, _, fixtures = installation
    assert run().returncode == 0
    previous = (prefix / "current").resolve()
    if failure == "checksum":
        (fixtures / "SHASUMS256.txt").write_text(
            "0" * 64 + "  node-v22.23.3-darwin-arm64.tar.gz\n"
        )
    result = run(INSTALL_TEST_FAIL=failure)
    assert result.returncode != 0
    assert "Installation failed during:" in result.stderr
    assert (prefix / "current").resolve() == previous
    assert list((prefix / "releases").iterdir()) == [previous]
    assert not (prefix / ".install-lock").exists()


def test_rejects_unsupported_platform_before_installing(installation):
    run, prefix, *_ = installation
    result = run(INSTALL_TEST_OS="Linux")
    assert result.returncode != 0 and "macOS only" in result.stderr
    assert not prefix.exists()


def test_does_not_replace_unrelated_command(installation):
    run, prefix, bin_dir, *_ = installation
    bin_dir.mkdir()
    command = bin_dir / "openbacktesting-studio"
    command.write_text("user command\n")
    result = run()
    assert result.returncode != 0 and "unrelated command" in result.stderr
    assert command.read_text() == "user command\n"
    assert not (prefix / "releases").exists()


def test_concurrent_install_is_rejected(installation):
    run, prefix, *_ = installation
    (prefix / ".install-lock").mkdir(parents=True)
    result = run()
    assert result.returncode != 0 and "Another installation" in result.stderr
    assert (prefix / ".install-lock").is_dir()
    assert not (prefix / "releases").exists()
