"""Check reviewed import boundaries without importing application code."""

from __future__ import annotations

import argparse
import ast
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST_ONLY = {'openbacktesting_studio', 'fastapi', 'uvicorn'}
UPPER = {'strategy', 'simulation', 'optimizer', 'portfolio', 'runtime', 'engine', 'lib', 'optimization', 'parallel'}


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f'{base}.{node.attr}' if base else None
    return None


def module_files(root):
    result = {}
    for folder in ('src', 'studio/src'):
        for path in (root / folder).rglob('*.py'):
            # Generated web assets are not Python application modules.
            parts = list(path.relative_to(root / folder).with_suffix('').parts)
            if parts[-1] == '__init__':
                parts.pop()
            result['.'.join(parts)] = path
    return result


def imports(tree, module, is_package, modules):
    aliases, edges, unresolved = {}, [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split('.')[0]] = alias.name if alias.asname else alias.name.split('.')[0]
                edges.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ''
            if node.level:
                package = module.split('.') if is_package else module.split('.')[:-1]
                base = '.'.join(package[:len(package) - node.level + 1] + ([base] if base else []))
            for alias in node.names:
                target = base + '.' + alias.name if base else alias.name
                aliases[alias.asname or alias.name] = target
                edges.append((target, node.lineno))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            name = dotted(node)
            if name and name.split('.')[0] in aliases:
                base, _, suffix = name.partition('.')
                target = aliases[base]
                if target in modules:
                    edges.append((target + '.' + suffix, node.lineno))
        if isinstance(node, ast.Call):
            call = dotted(node.func) or ''
            base, sep, tail = call.partition('.')
            resolved = aliases.get(base, base) + (sep + tail if sep else '')
            if resolved in {'importlib.import_module', '__import__', 'builtins.__import__', 'importlib.resources.files', 'importlib.resources.read_text', 'importlib.resources.read_binary'}:
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) and not node.args[0].value.startswith('.'):
                    edges.append((node.args[0].value, node.lineno))
                elif node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == '__package__':
                    edges.append((module if is_package else module.rpartition('.')[0], node.lineno))
                else:
                    unresolved.append({'line': node.lineno, 'expression': ast.unparse(node)})
    return aliases, sorted(set(edges)), unresolved


def inspect(root):
    root = root.resolve()
    modules = module_files(root)
    aliases, edges, limitations = {}, [], []
    findings = []

    def finding(rule, file, location, message, line=0):
        findings.append({'rule': rule, 'file': file, 'location': location, 'line': line,
                         'message': message, 'remedy': 'Use the documented boundary or review an exact exception with the maintainer.'})

    for module, path in sorted(modules.items()):
        name = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError as error:
            finding('syntax', name, 'parse', str(error), error.lineno)
            continue
        local, imported, dynamic = imports(tree, module, path.name == '__init__.py', modules)
        # Only top-level imports are exports; function-local aliases are not re-exports.
        top = ast.Module(body=[n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))], type_ignores=[])
        aliases[module] = imports(top, module, path.name == '__init__.py', modules)[0]
        edges += [{'file': name, 'module': module, 'target': target, 'line': line} for target, line in imported]
        limitations += [{'file': name, **row, 'reason': 'Dynamic import target cannot be proven statically; retain runtime and trusted-source checks.'} for row in dynamic]

    def resolve(target, visited=()):
        if target in visited:
            return target
        parent, _, leaf = target.rpartition('.')
        mapped = aliases.get(parent, {}).get(leaf)
        return resolve(mapped, (*visited, target)) if mapped and mapped != target else target

    manifest_path = root / 'docs/core/api-manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'objects': {}, 'scopes': []}
    public = {name for name, row in manifest['objects'].items() if row.get('status') in {'recommended', 'supported'}}
    public_modules = {name for name in manifest.get('scopes', []) if name in modules}
    public_modules.add('openbacktesting')
    rules_path = root / 'scripts/architecture-exceptions.json'
    registry = json.loads(rules_path.read_text()) if rules_path.exists() else {'exceptions': []}
    approved, used = {}, set()
    for row in registry['exceptions']:
        key = (row.get('file', ''), row.get('target', ''))
        if key in approved or not all(row.get(k) for k in ('file', 'target', 'reason', 'owner', 'removeWhen')) or any(c in ''.join(key) for c in '*?[]') or '..' in Path(key[0]).parts or Path(key[0]).is_absolute():
            finding('invalid-exception', 'scripts/architecture-exceptions.json', str(key), 'Exception must be unique, exact and justified')
        else:
            approved[key] = row
    for edge in edges:
        file, module, target = edge['file'], edge['module'], edge['target']
        resolved = resolve(target)
        edge['resolvedTarget'] = resolved
        if module.startswith('openbacktesting.') or module == 'openbacktesting':
            if target.split('.')[0] in HOST_ONLY or resolved.split('.')[0] in HOST_ONLY:
                finding('core-independent', file, target, f'Core must not depend on {target}', edge['line'])
            if module.startswith(('openbacktesting.data.', 'openbacktesting.broker.')) or module in {'openbacktesting.data', 'openbacktesting.broker'}:
                if target == 'openbacktesting.*':
                    finding('lower-layer', file, target, 'Wildcard imports hide high-level re-exports; import an explicit lower-level symbol', edge['line'])
                for candidate in (target, resolved):
                    parts = candidate.split('.')
                    if len(parts) > 1 and parts[0] == 'openbacktesting' and parts[1].lstrip('_') in UPPER:
                        finding('lower-layer', file, target, f'Lower layer depends on {target} (resolves to {resolved})', edge['line'])
                        break
        if module.startswith('openbacktesting_studio') and target.startswith('openbacktesting.'):
            if target in public or target in public_modules:
                continue
            key = (file, target)
            if key in approved:
                used.add(key)
            else:
                finding('studio-adapter', file, target, f'Unreviewed core internal dependency: {target}', edge['line'])
    for key in approved.keys() - used:
        finding('unused-exception', 'scripts/architecture-exceptions.json', '|'.join(key), 'Exact exception no longer matches an internal import')
    metadata = root / 'pyproject.toml'
    if metadata.exists():
        for dependency in tomllib.loads(metadata.read_text()).get('project', {}).get('dependencies', []):
            name = re.split(r'[<>=!~;\[\s]', dependency)[0].replace('-', '_').lower()
            if name in HOST_ONLY:
                finding('core-independent', 'pyproject.toml', dependency, f'Core runtime dependency includes host package: {dependency}')
    return {'schemaVersion': 1, 'findings': findings, 'limitations': limitations, 'edges': edges}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = inspect(args.root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for row in report['findings']:
            print(f"{row['file']}:{row['line']}: [{row['rule']}] {row['message']}; {row['remedy']}")
        for row in report['limitations']:
            print(f"Coverage limit: {row['file']}:{row['line']}: {row['expression']}")
        print(f"Architecture: {len(report['edges'])} edges; {len(report['findings'])} violations; {len(report['limitations'])} dynamic coverage limits")
    return bool(report['findings'])


if __name__ == '__main__':
    raise SystemExit(main())
