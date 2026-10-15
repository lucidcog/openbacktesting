"""The single check catalogue consumed by verification and maintenance."""

import os
import sys
from pathlib import Path

from harness_runtime import Check


def checks_for(root: Path):
    python = os.environ.get('HARNESS_PYTHON', f'{sys.version_info.major}.{sys.version_info.minor}')
    core = str(root / '.venv/bin/python')
    studio = str(root / 'studio/.venv/bin/python')
    all_profiles = ('docs', 'core', 'studio')
    root_needed = ('root-env',)
    npm = ('npm', '--prefix', 'studio/web')
    checks = [
        Check('root-env', ('uv', 'sync', '--locked', '--extra', 'test', '--group', 'docs', '--python', python), all_profiles, 'prepare', timeout=600),
        Check('language', (core, 'scripts/check_language.py'), all_profiles, needs=root_needed, maintenance=True),
        Check('package', (core, 'scripts/check_package.py'), ('docs', 'core'), needs=root_needed, maintenance=True),
        Check('indicator-drift', (core, 'scripts/generate_indicator_api.py', '--check'), ('docs', 'core'), needs=root_needed, maintenance=True),
        Check('reference-drift', (core, 'scripts/core_docs.py', '--check'), ('docs', 'core'), needs=root_needed, maintenance=True),
        Check('navigation', (core, 'scripts/check_harness_docs.py'), all_profiles, needs=root_needed, maintenance=True),
        Check('architecture', (core, 'scripts/check_architecture.py'), ('core', 'studio'), needs=root_needed, maintenance=True),
        Check('core-tests', (core, '-m', 'pytest', '-q', 'tests'), ('core',), needs=root_needed, timeout=1800),
        Check('core-selftest', (core, '-m', 'openbacktesting.test'), ('core',), needs=root_needed, timeout=1800),
        Check('docs-build', (core, '-m', 'mkdocs', 'build', '--strict'), ('docs',), needs=root_needed, maintenance=True),
        Check('docs-tests', (core, '-m', 'pytest', '-q', 'tests/test_user_documentation.py', 'tests/test_examples.py', 'tests/test_docs_discovery.py'), ('docs',), needs=root_needed, timeout=1200),
        Check('web-env', (*npm, 'ci', '--ignore-scripts'), ('studio',), 'prepare', timeout=600),
        Check('web-build', (*npm, 'run', 'build'), ('studio',), 'build', needs=('web-env',), timeout=900),
        Check('studio-env', ('uv', 'sync', '--project', 'studio', '--locked', '--extra', 'test', '--python', python), ('studio',), 'prepare', needs=('web-build',), timeout=600),
        Check('vendor', (studio, 'studio/scripts/check_vendor.py'), ('studio',), needs=('studio-env',), maintenance=True),
        Check('schema-drift', (studio, 'studio/scripts/export_schemas.py', '--check'), ('studio',), needs=('studio-env',), maintenance=True),
        Check('studio-tests', (studio, '-m', 'pytest', '-q', 'studio/tests'), ('studio',), needs=('studio-env',), timeout=1200),
        Check('web-types', (*npm, 'run', 'typecheck'), ('studio',), needs=('web-env',)),
        Check('web-lint', (*npm, 'run', 'lint'), ('studio',), needs=('web-env',)),
        Check('web-tests', (*npm, 'test'), ('studio',), needs=('web-env',)),
        Check('page-tools', ('node', '--test', 'tests/test_page_tools.cjs'), ('studio',), needs=('web-env',)),
        Check('browser-ready', ('node', 'studio/web/e2e/check-browser.mjs'), ('studio',), 'prepare', needs=('web-env',), remedy='Run npm --prefix studio/web exec -- playwright install chromium, then rerun.'),
        Check('browser-tests', (*npm, 'run', 'e2e'), ('studio',), needs=('studio-env', 'browser-ready'), timeout=600),
        Check('core-build', ('uv', 'build', '--no-sources', '--out-dir', 'dist'), ('full',), 'build', needs=('root-env',), timeout=600),
        Check('studio-build', ('uv', 'build', 'studio', '--out-dir', 'studio/dist'), ('full',), 'build', needs=('studio-env',), timeout=600),
        Check('distribution', (core, 'scripts/harness_distribution.py'), ('full',), needs=('core-build', 'studio-build'), timeout=600),
        Check('installation', (studio, 'studio/scripts/check_installation.py', '--python', python), ('full',), needs=('distribution',), timeout=1200),
    ]
    return checks
