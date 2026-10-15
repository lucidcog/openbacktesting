"""Schema check mode detects drift without approving or overwriting it."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location('schema_export', Path(__file__).parents[1] / 'scripts/export_schemas.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize('kind', ['matching', 'missing', 'extra', 'changed'])
def test_schema_check_is_read_only(tmp_path, kind):
    assert MODULE.main(['--directory', str(tmp_path)]) == 0
    file = next(tmp_path.glob('*.json'))
    if kind == 'missing':
        file.unlink()
    elif kind == 'extra':
        (tmp_path / 'unexpected.json').write_text('{}')
    elif kind == 'changed':
        file.write_text('{}')
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert MODULE.main(['--check', '--directory', str(tmp_path)]) == (0 if kind == 'matching' else 1)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_schema_fault_is_shared_by_all_entrypoints(tmp_path):
    import sys
    from dataclasses import replace
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'scripts'))
    from harness_checks import checks_for
    from harness_runtime import execute, select
    from doc_gardening import maintenance_checks
    MODULE.main(['--directory', str(tmp_path)])
    file = next(tmp_path.glob('*.json'))
    original = file.read_bytes()
    file.write_text('{}')
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    outputs = []
    groups = [select(checks_for(root), profile) for profile in ['studio', 'full']] + [maintenance_checks(root)]
    for index, checks in enumerate(groups):
        check = next(check for check in checks if check.id == 'schema-drift')
        check = replace(check, argv=(sys.executable, *check.argv[1:], '--directory', str(tmp_path)))
        evidence = tmp_path / f'evidence-{index}'
        evidence.mkdir()
        assert execute(check, root, evidence)['status'] == 'failed'
        outputs.append((evidence / 'schema-drift.stdout.log').read_text())
    assert len(set(outputs)) == 1
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()} == before
    file.write_bytes(original)
    assert MODULE.main(['--check', '--directory', str(tmp_path)]) == 0
