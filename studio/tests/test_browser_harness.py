"""Exercise cooperative Python network boundaries independently of browser routing."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parents[1] / 'web/e2e/guard'


@pytest.mark.parametrize('source', [
    "import socket; socket.create_connection(('192.0.2.1', 80), timeout=.1)",
    "import socket; socket.socket().connect_ex(('192.0.2.1', 80))",
    "import socket; socket.getaddrinfo('example.invalid', 80)",
])
def test_python_runtime_rejects_external_network(tmp_path, source):
    log = tmp_path / 'network.log'
    env = {**os.environ, 'PYTHONPATH': str(GUARD), 'HARNESS_NETWORK_LOG': str(log)}
    # A child interpreter models the inherited environment of real strategy workers.
    parent = 'import subprocess,sys; sys.exit(subprocess.call([sys.executable,"-c",sys.argv[1]]))'
    result = subprocess.run([sys.executable, '-c', parent, source], env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'forbids non-loopback' in result.stderr
    assert 'blocked' in log.read_text()


def test_guard_preserves_loopback(tmp_path):
    env = {**os.environ, 'PYTHONPATH': str(GUARD), 'HARNESS_NETWORK_LOG': str(tmp_path / 'network.log')}
    source = "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(); c=socket.create_connection(s.getsockname()); c.close(); s.close()"
    subprocess.run([sys.executable, '-c', source], env=env, check=True, timeout=10)
    assert not (tmp_path / 'network.log').exists()
