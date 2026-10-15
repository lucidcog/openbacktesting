"""Verify failure propagation and evidence against controlled subprocesses."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_checks import checks_for
from harness_runtime import Check, LOG_LIMIT, execute, redact, run_checks, select
from check_harness_docs import inspect


def command(name, source, **kwargs):
    return Check(name, (sys.executable, '-c', source), **kwargs)


def test_profiles_are_explicit_and_dependencies_deduplicated():
    checks = checks_for(ROOT)
    for profile in ('docs', 'core'):
        selected = select(checks, profile)
        assert not any(c.argv[0] in {'npm', 'node'} for c in selected)
        assert not any(c.id in {'studio-env', 'browser-tests'} for c in selected)
    full = select(checks, 'full')
    assert len({c.id for c in full}) == len(full)
    assert {'browser-tests', 'installation', 'core-tests'} <= {c.id for c in full}
    with pytest.raises(ValueError, match='Unknown profile'):
        select(checks, 'typo')
    with pytest.raises(ValueError, match='Cyclic'):
        select([command('a', '', needs=('a',))], 'full')


def test_failure_blocking_and_independent_checks(tmp_path):
    checks = [command('bad', 'raise SystemExit(4)'), command('dependent', 'raise AssertionError()', needs=('bad',)), command('good', 'print("ok")')]
    report, directory = run_checks(tmp_path, checks, 'full')
    assert [r['status'] for r in report['checks']] == ['failed', 'blocked', 'passed', 'passed']
    assert report['status'] == 'failed'
    assert report['checks'][0]['exitCode'] == 4
    assert json.loads((directory / 'result.json').read_text()) == report
    assert report['excludedChecks']
    second, _ = run_checks(tmp_path, [checks[-1]], 'full')
    assert second['runId'] != report['runId']
    assert (directory / 'bad.stderr.log').exists()


def test_missing_executable_is_environment_error(tmp_path):
    result = execute(Check('missing', ('/does/not/exist',)), tmp_path, tmp_path)
    assert result['status'] == 'error'
    assert result['exitCode'] is None


def test_timeout_stops_descendant_side_effects(tmp_path):
    marker = tmp_path / 'escaped'
    child = f'import time; time.sleep(0.8); open({str(marker)!r}, "w").write("bad")'
    parent = f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(20)'
    row = execute(command('timeout', parent, timeout=0.1), tmp_path, tmp_path)
    assert row['status'] == 'error' and 'Timed out' in row['reason']
    time.sleep(0.9)
    assert not marker.exists()


def test_dirty_sources_preserved_and_mutation_detected(tmp_path):
    source = tmp_path / 'source.py'
    source.write_text('user_change = 1\n')
    report, _ = run_checks(tmp_path, [command('read', 'pass')], 'core')
    assert report['status'] == 'passed'
    assert source.read_text() == 'user_change = 1\n'
    report, _ = run_checks(tmp_path, [command('write', 'open("source.py", "w").write("unexpected = 2")')], 'core')
    assert report['status'] == 'failed'
    assert report['checks'][-1]['files'] == ['source.py']
    assert source.read_text() == 'unexpected = 2'


def test_bounded_logs_redact_credentials(tmp_path):
    source = 'print("http://127.0.0.1:123/#token=private-secret"); print("Cookie: private-cookie"); print("x" * 2000000)'
    row = execute(command('logs', source), tmp_path, tmp_path)
    text = (tmp_path / 'logs.stdout.log').read_text()
    assert row['truncated'] and len(text) < LOG_LIMIT + 100
    assert 'private-secret' not in text and 'private-cookie' not in text
    assert '[OUTPUT TRUNCATED]' in text
    assert 'secret-value' not in redact('{"csrf": "secret-value", "token": "secret-value"}')


@pytest.mark.skipif(os.name != 'posix', reason='POSIX process groups')
def test_cancel_saves_report_and_stops_children(tmp_path):
    script = f'''import signal,sys
sys.path.insert(0,{str(ROOT / 'scripts')!r})
from harness_runtime import run_checks,Check
from pathlib import Path
def cancel(*args): raise KeyboardInterrupt
signal.signal(signal.SIGTERM,cancel)
run_checks(Path({str(tmp_path)!r}),[Check('wait',(sys.executable,'-c','import time; time.sleep(30)'))],'full')
'''
    process = subprocess.Popen([sys.executable, '-c', script], stdout=subprocess.PIPE, text=True)
    try:
        assert '[full] wait' in process.stdout.readline()
        time.sleep(0.1)
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=10)
        report = json.loads(next((tmp_path / '.verification/harness').glob('*/result.json')).read_text())
        assert report['status'] == 'cancelled'
        assert report['checks'][0]['status'] == 'cancelled'
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_navigation_ignores_examples_but_catches_real_links(tmp_path):
    for name in ('AGENTS.md', 'docs/core/development.md', 'docs/core/harness.md', 'docs/core/harness-quality.md'):
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('`[example](URL)`\n')
    assert inspect(tmp_path) == []
    (tmp_path / 'AGENTS.md').write_text('[broken](missing.md)\n')
    assert inspect(tmp_path)[0]['location'] == 'missing.md'


def test_json_credentials_are_removed():
    assert 'synthetic-cookie' not in redact('{"cookie": "synthetic-cookie"}')
    assert 'synthetic-bearer' not in redact('{"authorization": "Bearer synthetic-bearer"}')
