"""Validate required matrix status and read-only workflow contracts locally."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_ci_matrix_and_fail_closed_summary():
    workflow = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())
    assert workflow['permissions'] == {'contents': 'read'}
    events = workflow.get('on', workflow.get(True))
    assert set(events) == {'push', 'pull_request', 'workflow_dispatch'}
    jobs = workflow['jobs']
    assert jobs['verify']['strategy']['matrix']['include'] == [{'python': '3.12', 'profile': 'full'}, {'python': '3.13', 'profile': 'core'}, {'python': '3.14', 'profile': 'core'}]
    summary = jobs['summary']
    assert summary['if'] == 'always()' and summary['needs'] == ['verify']
    command = summary['steps'][0]['run']
    import os
    import subprocess
    for status in ['success', 'failure', 'cancelled', 'skipped']:
        result = subprocess.run(['sh', '-c', command], env={**os.environ, 'RESULT': status})
        assert (result.returncode == 0) == (status == 'success')
    uploads = [s for s in jobs['verify']['steps'] if s.get('uses', '').startswith('actions/upload-artifact')]
    assert uploads[0]['if'] == 'always()' and uploads[0]['with']['retention-days'] == 14


def test_maintenance_schedule_and_no_mutation():
    text = (ROOT / '.github/workflows/maintenance.yml').read_text()
    workflow = yaml.safe_load(text)
    events = workflow.get('on', workflow.get(True))
    assert set(events) == {'schedule', 'workflow_dispatch'}
    assert len(events['schedule'][0]['cron'].split()) == 5
    assert set(workflow['permissions'].values()) == {'read'}
    assert 'scripts/doc_gardening.py --previous' in text
    assert all(command not in text for command in ['git push', 'gh pr create', 'gh pr merge'])
