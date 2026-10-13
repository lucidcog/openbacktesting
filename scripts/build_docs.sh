#!/usr/bin/env bash
# Build the static site with isolated, locked documentation dependencies.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -m venv build/docs-tools
build/docs-tools/bin/python -m pip install --disable-pip-version-check 'uv==0.10.4'

UV_PROJECT_ENVIRONMENT="$PWD/build/docs-env" \
  build/docs-tools/bin/uv run --locked --only-group docs mkdocs build --strict "$@"
