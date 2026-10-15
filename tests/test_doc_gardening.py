"""Maintenance identity and history must survive unrelated source movement."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import doc_gardening as garden


def test_semantic_identity_ignores_line_numbers():
    assert garden.identify('arch', 'import', 'a.py', 'a.py:12: bad') == garden.identify('arch', 'import', 'a.py', 'a.py:99: bad')
    assert garden.identify('docs', 'link', 'a.md', 'missing.md') != garden.identify('docs', 'link', 'a.md', 'other.md')


def test_history_requires_valid_evidence():
    rows = [{'id': 'a'}, {'id': 'b'}]
    for previous in [None, {}, {'schemaVersion': 1, 'findings': ['broken'], 'checks': []}]:
        assert garden.compare(rows, previous)[0] == 'unknown'
    state, resolved, current = garden.compare(rows, {'schemaVersion': 1, 'findings': [{'id': 'a'}, {'id': 'c'}], 'checks': []})
    assert state == 'compared' and resolved == [{'id': 'c'}]
    assert [r['history'] for r in current] == ['persistent', 'new']


def test_catalogue_shares_schema_check():
    root = Path(__file__).resolve().parents[1]
    selected = garden.maintenance_checks(root)
    assert {'language', 'package', 'navigation', 'architecture', 'schema-drift', 'docs-build'} <= {c.id for c in selected}
    actual = next(c for c in selected if c.id == 'schema-drift')
    assert actual.argv == next(c for c in garden.checks_for(root) if c.id == actual.id).argv
    assert '--check' in actual.argv


def test_link_fault_and_repair_preserve_files(tmp_path):
    for name in ['AGENTS.md', 'docs/core/development.md', 'docs/core/harness.md', 'docs/core/harness-quality.md']:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[Broken](missing.md)\n' if name == 'AGENTS.md' else '# OK\n')
    before = {p: p.read_bytes() for p in tmp_path.rglob('*.md')}
    report = {'runId': 'test', 'commit': None, 'status': 'failed', 'checks': [{'id': 'navigation', 'status': 'failed', 'evidence': [], 'remedy': 'Fix link'}]}
    bad = garden.summarize(tmp_path, report, tmp_path)
    assert len(bad['findings']) == 1
    assert {p: p.read_bytes() for p in before} == before
    (tmp_path / 'AGENTS.md').write_text('\n\n[Broken](missing.md)\n')
    shifted = garden.summarize(tmp_path, report, tmp_path, bad)
    assert shifted['findings'][0]['history'] == 'persistent'
    report['checks'][0]['status'] = 'blocked'
    blocked = garden.summarize(tmp_path, report, tmp_path, bad)
    assert not blocked['resolved']
    report['checks'][0]['status'] = 'passed'
    fixed = garden.summarize(tmp_path, report, tmp_path, bad)
    assert len(fixed['resolved']) == 1


def test_stale_registration_has_a_stable_local_finding(tmp_path):
    log = tmp_path / 'language.stderr.log'
    log.write_text('Unused file exemption: docs/deleted.md\n')
    run = {'runId': 'test', 'commit': None, 'status': 'failed', 'checks': [{'id': 'language', 'status': 'failed', 'evidence': [log.name], 'remedy': 'Review exact registration'}]}
    report = garden.summarize(tmp_path, run, tmp_path)
    assert report['findings'][0]['file'] == 'docs/deleted.md'
    assert report['findings'][0]['severity'] == 'medium'
    assert log.read_text() == 'Unused file exemption: docs/deleted.md\n'
