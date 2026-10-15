"""Validate exactly the artifacts belonging to the current project versions."""

import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def artifacts(project, directory):
    metadata = tomllib.loads((project / 'pyproject.toml').read_text())['project']
    stem = metadata['name'].replace('-', '_') + '-' + metadata['version']
    paths = [directory / (stem + '-py3-none-any.whl'), directory / (stem + '.tar.gz')]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f'Missing current-version artifact: {path}')
    return paths


def main():
    core = artifacts(ROOT, ROOT / 'dist')
    studio = artifacts(ROOT / 'studio', ROOT / 'studio/dist')
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_package.py'),
                    *[arg for path in core for arg in ('--artifact', str(path))]], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / 'studio/scripts/check_distribution.py'),
                    *map(str, studio)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
