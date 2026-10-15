"""Check repository knowledge links without importing application dependencies."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def inspect(root):
    paths = {root / 'AGENTS.md', root / 'docs/core/development.md', root / 'docs/core/harness.md', root / 'docs/core/harness-quality.md'}
    for folder in ('docs/research', 'openspec'):
        paths.update((root / folder).rglob('*.md'))
    findings = []
    for path in sorted(paths):
        name = path.relative_to(root).as_posix()
        if not path.is_file():
            findings.append({'rule': 'knowledge-file', 'file': name, 'location': name, 'message': 'Required knowledge entry is missing'})
            continue
        text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
        text = re.sub(r'(`+).*?\1', '', text)
        for match in re.finditer(r'\]\(([^\s)]+)', text):
            link = match.group(1).strip('<>')
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
                findings.append({'rule': 'knowledge-link', 'file': name, 'location': link,
                                 'message': f'Broken local link: {link}'})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    findings = inspect(args.root.resolve())
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        for row in findings:
            print(f"{row['file']}: {row['message']}; repair the reference or restore its intended source")
        if not findings:
            print('Knowledge navigation check passed')
    return bool(findings)


if __name__ == '__main__':
    raise SystemExit(main())
