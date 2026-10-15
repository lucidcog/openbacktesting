"""Run the same explicit verification profiles locally and in CI."""

import argparse
import json
import signal
from pathlib import Path

from harness_checks import checks_for
from harness_runtime import run_checks, select

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('docs', 'core', 'studio', 'full'), default='full')
    parser.add_argument('--list', action='store_true', help='Print the selected check IDs without executing them')
    args = parser.parse_args(argv)
    checks = select(checks_for(ROOT), args.profile)
    if args.list:
        print(json.dumps([c.id for c in checks], indent=2))
        return 0

    def cancel(signum, frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, cancel)
    try:
        report, _ = run_checks(ROOT, checks, args.profile)
        return 0 if report['status'] == 'passed' else 1
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == '__main__':
    raise SystemExit(main())
