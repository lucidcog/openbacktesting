"""Read-only maintenance using the verification catalogue and optional prior evidence."""
import argparse
import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path

from check_architecture import inspect as architecture
from check_harness_docs import inspect as navigation
from harness_checks import checks_for
from harness_runtime import run_checks, select

ROOT = Path(__file__).resolve().parents[1]


def maintenance_checks(root):
    checks = checks_for(root)
    # Selection expands the same preparation dependencies as verification.
    return select([replace(c, profiles=('docs',) if c.maintenance else ()) for c in checks], 'docs')


def identify(check, rule, file, location):
    semantic = re.sub(r':\d+(?::\d+)?(?=:|\s|$)', ':LINE', location)
    return hashlib.sha256(json.dumps([check, rule, file, semantic], ensure_ascii=True).encode()).hexdigest()[:20]


def compare(findings, previous):
    if not isinstance(previous, dict) or previous.get('schemaVersion') != 1 or not isinstance(previous.get('findings'), list) or not isinstance(previous.get('checks'), list):
        return 'unknown', [], [dict(row, history='unknown') for row in findings]
    if any(not isinstance(row, dict) or not isinstance(row.get('id'), str) for row in previous['findings']):
        return 'unknown', [], [dict(row, history='unknown') for row in findings]
    old = {row['id']: row for row in previous['findings']}
    current = {row['id'] for row in findings}
    return 'compared', [row for key, row in old.items() if key not in current], [dict(row, history='persistent' if row['id'] in old else 'new') for row in findings]


def summarize(root, run, directory, previous=None):
    findings = []
    for check in run['checks']:
        if check['status'] == 'passed':
            continue
        rows = []
        if check['status'] == 'failed' and check['id'] == 'navigation':
            rows = navigation(root)
        elif check['status'] == 'failed' and check['id'] == 'architecture':
            rows = architecture(root)['findings']
        if not rows:
            diagnostics = '\n'.join((directory / name).read_text() for name in check['evidence'])
            if check['status'] == 'failed' and check['id'] == 'schema-drift':
                names = re.search(r'^Schema drift: (.+)$', diagnostics, re.M)
                if names:
                    rows = [{'rule': 'schema-drift', 'file': 'studio/src/openbacktesting_studio/protocol/schemas/' + name,
                             'location': name, 'message': 'Schema differs from its protocol model'} for name in names[1].split(', ')]
            if not rows and check['status'] == 'failed' and check['id'] in {'language', 'package', 'indicator-drift', 'reference-drift'}:
                for message in diagnostics.splitlines():
                    if not message.strip():
                        continue
                    paths = re.findall(r'[\w./-]+\.(?:py|md|json|ya?ml|toml|html|css|tsx?)\b', message)
                    file = paths[0] if paths else {'language': 'scripts/language-exceptions.json', 'package': 'extraction-manifest.json',
                                                  'indicator-drift': 'docs/core/api-manifest.json', 'reference-drift': 'docs/core/reference'}[check['id']]
                    semantic = re.sub(r':\d+(?::\d+)?', ':LINE', message)
                    rows.append({'rule': check['id'], 'file': file, 'location': semantic, 'message': message})
            if not rows:
                rows = [{'rule': check['id'], 'file': check.get('files', [''])[0] if check.get('files') else 'scripts/harness_checks.py',
                         'location': check['id'], 'message': diagnostics.strip()[:8192] or check.get('reason', 'Check failed')}]
        for row in rows:
            findings.append({**row, 'id': identify(check['id'], row['rule'], row['file'], row['location']),
                             'check': check['id'], 'severity': 'high' if check['id'] in {'source-integrity', 'architecture', 'package', 'schema-drift', 'root-env', 'studio-env', 'web-env'} else 'medium',
                             'evidence': check['evidence'], 'candidateFix': ('Maintainer review required; do not refresh contracts or provenance solely to pass. ' if check['id'] in {'schema-drift', 'package', 'architecture', 'root-env', 'studio-env', 'web-env'} else '') + check['remedy']})
    history, resolved, findings = compare(findings, previous)
    # A blocked or errored check cannot prove that its old findings were resolved.
    passed = {row['id'] for row in run['checks'] if row['status'] == 'passed'}
    uncertain = [dict(row, history='unknown') for row in resolved if row.get('check') not in passed]
    resolved = [row for row in resolved if row.get('check') in passed]
    return {'schemaVersion': 1, 'runId': run['runId'], 'commit': run['commit'], 'status': run['status'],
            'comparison': history, 'findings': findings + uncertain, 'resolved': resolved,
            'checks': run['checks'], 'limitations': ['Static imports cannot prove all runtime dependencies.',
            'No previous valid report means trend is unknown. Candidate fixes require review.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    previous = None
    history_reason = 'First baseline: no previous report requested'
    if args.previous:
        try:
            previous = json.loads(args.previous.read_text())
            history_reason = 'Previous report loaded'
        except (OSError, ValueError) as error:
            history_reason = f'Previous report could not be read: {type(error).__name__}'
    run, directory = run_checks(ROOT, maintenance_checks(ROOT), 'maintenance')
    report = summarize(ROOT, run, directory, previous)
    report['comparisonReason'] = history_reason if previous is None or report['comparison'] == 'compared' else 'Previous report has an invalid schema'
    (directory / 'maintenance.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Maintenance findings', '', f"Status: {report['status']}; history: {report['comparison']}", '']
    for row in report['findings']:
        lines += [f"- {row['severity']} `{row['id']}` ({row['history']}): {row['file']} — {row['message']}", f"  Candidate fix: {row['candidateFix']}"]
    lines += ['', f"Resolved with passing checks: {len(report['resolved'])}.", 'No repository files were repaired automatically.']
    (directory / 'maintenance.md').write_text('\n'.join(lines) + '\n')
    return 0 if run['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
