"""Inject real dependency violations rather than mirroring the rule implementation."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_architecture import inspect


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_core_host_dependencies_and_metadata(tmp_path):
    put(tmp_path, 'src/openbacktesting/feature.py', 'def run():\n import fastapi as api\n')
    put(tmp_path, 'pyproject.toml', '[project]\ndependencies=["openbacktesting-studio>=0.1"]\n')
    report = inspect(tmp_path)
    assert len(report['findings']) == 2
    assert all(row['rule'] == 'core-independent' for row in report['findings'])


def test_relative_reexport_alias_and_type_only_import(tmp_path):
    put(tmp_path, 'src/openbacktesting/__init__.py', 'from .bridge import Backtest\n')
    put(tmp_path, 'src/openbacktesting/bridge.py', 'from .simulation.core import Backtest\n')
    put(tmp_path, 'src/openbacktesting/data/new.py', 'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n from .. import Backtest as B\n')
    report = inspect(tmp_path)
    rows = [r for r in report['findings'] if r['rule'] == 'lower-layer']
    assert len(rows) == 1
    assert 'simulation.core.Backtest' in rows[0]['message']


def test_module_attribute_access_and_dynamic_import(tmp_path):
    put(tmp_path, 'src/openbacktesting/__init__.py', 'from .simulation.core import Backtest\n')
    put(tmp_path, 'src/openbacktesting/data/new.py', 'import openbacktesting as bt\nx = bt.Backtest\nfrom importlib import import_module as load\nload("openbacktesting.runtime")\nload(user_value)\n')
    report = inspect(tmp_path)
    assert len([r for r in report['findings'] if r['rule'] == 'lower-layer']) == 2
    assert len(report['limitations']) == 1
    assert report['limitations'][0]['expression'] == 'load(user_value)'


def test_legal_type_dependency(tmp_path):
    put(tmp_path, 'src/openbacktesting/data/new.py', 'from openbacktesting.indicators.types import IndicatorHandle\n')
    assert not inspect(tmp_path)['findings']


def test_exact_exceptions_do_not_expand_and_expire(tmp_path):
    name = 'studio/src/openbacktesting_studio/execution/worker.py'
    target = 'openbacktesting.strategy.inputs.resolve_request'
    put(tmp_path, name, f'from {target.rpartition(".")[0]} import resolve_request\n')
    assert inspect(tmp_path)['findings'][0]['rule'] == 'studio-adapter'
    row = {'file': name, 'target': target, 'reason': 'Reviewed adapter', 'owner': 'Maintainers', 'removeWhen': 'Public API available'}
    put(tmp_path, 'scripts/architecture-exceptions.json', json.dumps({'exceptions': [row]}))
    assert not inspect(tmp_path)['findings']
    put(tmp_path, name.replace('worker.py', 'new.py'), f'from {target.rpartition(".")[0]} import resolve_request\n')
    assert inspect(tmp_path)['findings'][0]['rule'] == 'studio-adapter'
    put(tmp_path, name, '')
    assert 'unused-exception' in {r['rule'] for r in inspect(tmp_path)['findings']}
    row['file'] = 'studio/**'
    put(tmp_path, 'scripts/architecture-exceptions.json', json.dumps({'exceptions': [row]}))
    assert 'invalid-exception' in {r['rule'] for r in inspect(tmp_path)['findings']}


def test_repository_has_only_reviewed_adapters():
    report = inspect(ROOT)
    assert not report['findings']
    assert len(report['limitations']) == 1
    assert report['limitations'][0]['file'].endswith('execution/worker.py')


def test_core_resource_and_hidden_wildcard_edges(tmp_path):
    put(tmp_path, 'src/openbacktesting/data/new.py', 'from importlib.resources import files\nfiles("openbacktesting_studio")\nfrom openbacktesting import *\n')
    assert {row['rule'] for row in inspect(tmp_path)['findings']} == {'core-independent', 'lower-layer'}
