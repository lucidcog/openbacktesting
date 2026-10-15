"""Generate Studio schemas explicitly, or check drift without modifying files."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'src/openbacktesting_studio/protocol/schemas'


def expected_schemas():
    from openbacktesting_studio.protocol import SCHEMAS
    return {f'{name}.json': json.dumps({
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        **model.model_json_schema(),
    }, indent=2) + '\n' for name, model in SCHEMAS.items()}


def differences(directory, expected):
    actual = {p.name: p.read_text() for p in directory.glob('*.json')}
    return [name for name in sorted(actual.keys() | expected.keys()) if actual.get(name) != expected.get(name)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--directory', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    expected = expected_schemas()
    if args.check:
        changed = differences(args.directory, expected)
        if changed:
            print('Schema drift: ' + ', '.join(changed))
            print('Review protocol changes, then explicitly run studio/scripts/export_schemas.py.')
            return 1
        print('Studio schema drift check passed')
        return 0
    args.directory.mkdir(parents=True, exist_ok=True)
    for name, content in expected.items():
        (args.directory / name).write_text(content)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
