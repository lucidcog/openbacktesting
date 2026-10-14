#!/bin/bash
# Install Studio without requiring an existing Python, Node, Git, or sudo setup.
# Keep execution in main so an incomplete piped download cannot start installation.
set -euo pipefail

usage() {
    cat <<'HELP'
Install OpenBacktesting Studio on macOS (Apple Silicon or Intel).

Usage: bash install-studio.sh [options]
  --no-launch          Install without starting Studio
  --source DIRECTORY   Build a local checkout instead of downloading main
  --prefix DIRECTORY   Installation directory (default: ~/.local/share/openbacktesting-studio)
  --bin-dir DIRECTORY  Command directory (default: ~/.local/bin)
  --no-shortcut        Do not create ~/Applications/OpenBacktesting Studio.command
  --help               Show this help

Repeat the command to update. A failed build leaves the previous installation active.
HELP
}

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }
download() { curl --proto '=https' --tlsv1.2 -fsSL --retry 3 --connect-timeout 20 "$1" -o "$2"; }

cleanup() {
    local status=$?
    trap - EXIT
    [ -z "${scratch:-}" ] || rm -rf "$scratch"
    if [ "$status" -ne 0 ]; then
        [ -z "${release:-}" ] || [ "${activated:-0}" = 1 ] || rm -rf "$release"
        printf '\nInstallation failed during: %s. Fix the reported error and run the installer again.\n' "${step:-setup}" >&2
    fi
    [ -z "${lock:-}" ] || rmdir "$lock"
    exit "$status"
}

main() {
    local prefix="${HOME}/.local/share/openbacktesting-studio"
    local bin_dir="${HOME}/.local/bin" source_dir='' launch=1 shortcut=1 arch uv node_archive
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --help) usage; return ;;
            --no-launch) launch=0; shift ;;
            --no-shortcut) shortcut=0; shift ;;
            --prefix|--bin-dir|--source)
                [ "$#" -ge 2 ] && [ -n "$2" ] || fail "$1 needs a directory."
                case "$1" in
                    --prefix) prefix=$2 ;;
                    --bin-dir) bin_dir=$2 ;;
                    --source) source_dir=$2 ;;
                esac
                shift 2 ;;
            *) fail "Unknown option: $1 (see --help)." ;;
        esac
    done
    [ "$(uname -s)" = Darwin ] || fail 'This installer currently supports macOS only.'
    case "$(uname -m)" in
        arm64) arch=arm64 ;;
        x86_64) arch=x64 ;;
        *) fail 'Unsupported Mac architecture.' ;;
    esac
    [ "$(id -u)" -ne 0 ] || fail 'Run this installer as your normal user, without sudo.'
    case "$prefix:$bin_dir" in *$'\n'*) fail 'Directory paths must not contain newlines.' ;; esac
    if [ -n "$source_dir" ]; then
        source_dir=$(cd "$source_dir" && pwd -P)
        [ -f "$source_dir/studio/hatch_build.py" ] || fail '--source must point to an OpenBacktesting checkout.'
    fi
    mkdir -p "$prefix" "$bin_dir"
    prefix=$(cd "$prefix" && pwd -P)
    bin_dir=$(cd "$bin_dir" && pwd -P)
    # Never replace unrelated command files or installation directories.
    if [ -e "$bin_dir/openbacktesting-studio" ] || [ -L "$bin_dir/openbacktesting-studio" ]; then
        [ -L "$bin_dir/openbacktesting-studio" ] &&
            [ "$(readlink "$bin_dir/openbacktesting-studio")" = "$prefix/studio" ] ||
            fail "An unrelated command exists at $bin_dir/openbacktesting-studio. Use --bin-dir."
    fi
    if [ -e "$prefix/current" ] || [ -L "$prefix/current" ]; then
        [ -L "$prefix/current" ] || fail "$prefix/current is not a managed symlink."
    fi
    if [ -e "$prefix/studio" ]; then
        grep -q '^# OpenBacktesting Studio managed launcher$' "$prefix/studio" ||
            fail "$prefix/studio is not a managed launcher."
    fi
    local app="$HOME/Applications/OpenBacktesting Studio.command"
    if [ "$shortcut" = 1 ] && [ -e "$app" ]; then
        grep -q '^# OpenBacktesting Studio managed launcher$' "$app" ||
            fail "An unrelated file exists at $app. Use --no-shortcut."
    fi
    mkdir "$prefix/.install-lock" 2>/dev/null || fail "Another installation may be running. If it was interrupted, remove $prefix/.install-lock and retry."
    lock="$prefix/.install-lock"
    trap cleanup EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    scratch=$(mktemp -d "${TMPDIR:-/tmp}/openbacktesting-install.XXXXXX")
    mkdir -p "$prefix/releases"
    release=$(mktemp -d "$prefix/releases/install.XXXXXX")
    step='downloading Studio'
    printf '[1/5] Preparing Studio source...\n'
    mkdir "$scratch/source"
    if [ -n "$source_dir" ]; then
        # Copy only build inputs; never build in or overwrite the user's checkout.
        tar -C "$source_dir" --exclude=node_modules --exclude=.venv --exclude=__pycache__ \
            --exclude=dist --exclude=.openbacktesting -cf - \
            pyproject.toml README.md LICENSE src examples studio/pyproject.toml studio/README.md \
            studio/LICENSE studio/hatch_build.py studio/src studio/web studio/vendor studio/vendor-metadata \
            studio/tests/fixtures |
            tar -xf - -C "$scratch/source"
    else
        download 'https://codeload.github.com/lucidcog/openbacktesting/tar.gz/refs/heads/main' "$scratch/source.tar.gz"
        tar -xzf "$scratch/source.tar.gz" -C "$scratch/source" --strip-components=1
    fi
    [ -f "$scratch/source/studio/hatch_build.py" ] || fail 'Downloaded source does not contain Studio.'

    step='preparing Python'
    printf '[2/5] Preparing a private Python environment...\n'
    download 'https://astral.sh/uv/install.sh' "$scratch/uv-install.sh"
    UV_UNMANAGED_INSTALL="$scratch/uv" sh "$scratch/uv-install.sh"
    uv="$scratch/uv/uv"
    export UV_PYTHON_INSTALL_DIR="$prefix/python"
    export UV_PYTHON_PREFERENCE=only-managed UV_NO_CONFIG=1
    "$uv" venv --python 3.12 "$release/venv"

    step='preparing build tools'
    printf '[3/5] Preparing private build tools...\n'
    download 'https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt' "$scratch/SHASUMS256.txt"
    node_archive=$(awk -v suffix="-darwin-$arch.tar.gz" '$2 ~ (suffix "$") {print $2}' "$scratch/SHASUMS256.txt")
    [[ "$node_archive" =~ ^node-v22\.[0-9]+\.[0-9]+-darwin-(arm64|x64)\.tar\.gz$ ]] || fail 'Cannot identify the Node.js download.'
    download "https://nodejs.org/dist/latest-v22.x/$node_archive" "$scratch/$node_archive"
    (cd "$scratch"; awk -v name="$node_archive" '$2 == name' SHASUMS256.txt | shasum -a 256 -c -)
    mkdir "$scratch/node"
    tar -xzf "$scratch/$node_archive" -C "$scratch/node" --strip-components=1
    export PATH="$scratch/node/bin:$PATH"

    step='building and installing Studio'
    printf '[4/5] Building and installing Studio (this can take a few minutes)...\n'
    npm --prefix "$scratch/source/studio/web" ci --ignore-scripts --no-audit --no-fund
    npm --prefix "$scratch/source/studio/web" run build
    "$uv" pip install --python "$release/venv/bin/python" "$scratch/source" "$scratch/source/studio"
    "$release/venv/bin/python" -m openbacktesting_studio.cli --help >/dev/null

    step='creating launchers'
    printf '[5/5] Creating the Studio launcher...\n'
    # Keep examples outside version directories; updates must preserve edits and run history.
    mkdir -p "$prefix/examples"
    for example in "$scratch/source/examples/strategies/"*.py; do
        local target="$prefix/examples/$(basename "$example")"
        if [ ! -e "$target" ] && [ ! -L "$target" ]; then
            cp "$example" "$prefix/examples/"
        fi
    done
    {
        printf '#!/bin/bash\n# OpenBacktesting Studio managed launcher\n'
        printf 'studio_root=%q\n' "$prefix"
        cat <<'LAUNCHER'
if [ "$#" -eq 0 ]; then
    set -- "$studio_root/examples"
fi
studio_version=$(cd "$studio_root/current" && pwd -P) || exit 1
exec "$studio_version/venv/bin/python" -m openbacktesting_studio.cli "$@"
LAUNCHER
    } > "$scratch/launcher"
    chmod +x "$scratch/launcher"
    # The environment stays at its original path so generated Python entrypoints remain valid.
    "$release/venv/bin/python" - "$prefix" "$release" <<'PY'
import os
import sys
from pathlib import Path
root, release = map(Path, sys.argv[1:])
pending = root / '.current-next'
pending.unlink(missing_ok=True)
pending.symlink_to(release)
os.replace(pending, root / 'current')
PY
    activated=1
    cp "$scratch/launcher" "$prefix/studio"
    [ -L "$bin_dir/openbacktesting-studio" ] || ln -s "$prefix/studio" "$bin_dir/openbacktesting-studio"
    if [ "$shortcut" = 1 ]; then
        mkdir -p "$HOME/Applications"
        cp "$scratch/launcher" "$app"
        printf '\nNext time, double-click: %s\n' "$app"
    fi
    printf '\nStudio is installed. Terminal launcher: %s\n' "$prefix/studio"
    # Release the installer lock and temporary build tools before running the server.
    rm -rf "$scratch"
    scratch=''
    rmdir "$lock"
    lock=''
    trap - EXIT INT TERM
    if [ "$launch" = 1 ]; then
        "$prefix/studio"
    fi
}

main "$@"
