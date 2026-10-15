"""Retrieve optional evidence from the latest completed maintenance run, read-only."""
import json
import subprocess
from pathlib import Path


def main():
    destination = Path('.verification/previous')
    destination.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(['gh', 'run', 'list', '--workflow', 'maintenance.yml', '--branch', 'main', '--status', 'completed', '--limit', '1', '--json', 'databaseId'], capture_output=True, text=True, check=True, timeout=30)
        rows = json.loads(result.stdout)
        if not rows:
            raise ValueError('No previous completed run')
        subprocess.run(['gh', 'run', 'download', str(rows[0]['databaseId']), '--name', 'maintenance', '--dir', str(destination / 'download')], capture_output=True, check=True, timeout=60)
        candidates = sorted((destination / 'download').rglob('maintenance.json'))
        if len(candidates) != 1:
            raise ValueError('Previous artifact is missing or ambiguous')
        report = json.loads(candidates[0].read_text())
        (destination / 'maintenance.json').write_text(json.dumps(report))
        print('Previous maintenance evidence retrieved')
    except (OSError, ValueError, subprocess.SubprocessError):
        (destination / 'maintenance.json').unlink(missing_ok=True)
        print('Previous evidence unavailable; history will be unknown')


if __name__ == '__main__':
    main()
