"""Managed short processes with bounded output and process-group cleanup."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
from collections import deque
from importlib.metadata import version
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from openbacktesting_studio.workspace import WorkspaceError


class Tail:
    def __init__(self, limit=1024 * 1024):
        self.limit = limit
        self.parts = deque()
        self.size = 0
        self.truncated = False

    def read(self, stream):
        while data := stream.read(65536):
            self.parts.append(data)
            self.size += len(data)
            while self.size > self.limit:
                first = self.parts.popleft()
                keep = max(0, len(first) - (self.size - self.limit))
                self.size -= len(first)
                if keep:
                    self.parts.appendleft(first[-keep:])
                    self.size += keep
                self.truncated = True
        stream.close()

    def export(self):
        return {
            "text": b"".join(self.parts).decode("utf-8", errors="replace"),
            "truncated": self.truncated,
        }


class ManagedProcess:
    def __init__(self, command, *, cwd=None):
        kwargs = (
            {"start_new_session": True}
            if os.name != "nt"
            else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        )
        self.process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs,
        )
        self.stdout, self.stderr = Tail(), Tail()
        self.readers = [
            threading.Thread(target=tail.read, args=(stream,), daemon=True)
            for tail, stream in [
                (self.stdout, self.process.stdout),
                (self.stderr, self.process.stderr),
            ]
        ]
        for reader in self.readers:
            reader.start()

    def terminate(self, grace=3):
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                capture_output=True,
                timeout=grace + 5,
                check=False,
            )
        else:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            try:
                self.process.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                pass
            # Also reclaim descendants after the leader exits.
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.process.wait(timeout=5)

    def wait(self, timeout=None):
        try:
            code = self.process.wait(timeout=timeout)
            if os.name != "nt":
                self.terminate(grace=0)
        except subprocess.TimeoutExpired:
            self.terminate()
            raise WorkspaceError("WorkerTimeout", "Worker exceeded its time limit", 422)
        finally:
            for reader in self.readers:
                reader.join(timeout=1)
        return code


def probe(python):
    try:
        result = subprocess.run(
            [python, "-m", "openbacktesting_studio.execution.worker", "--probe"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode:
            raise ValueError("Install a compatible openbacktesting-studio into this interpreter")
        info = json.loads(result.stdout)
        if info["protocolVersion"] != 1 or Version(info["coreVersion"]) not in SpecifierSet(
            ">=0.2.1,<0.3"
        ):
            raise ValueError("Worker protocol or framework version is incompatible")
        if info["studioVersion"] != version("openbacktesting-studio"):
            raise ValueError("Host and worker Studio versions must match")
        if Version(info["pythonVersion"]) not in SpecifierSet(">=3.12,<3.15"):
            raise ValueError("Python version is unsupported")
        return info | {"compatible": True, "executable": python}
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        return {"compatible": False, "executable": python, "message": str(error)}


def discover(python, snapshot, *, timeout=30):
    directory = Path(snapshot["directory"])
    request = directory.parent / (directory.name + "-discover-request.json")
    response = directory.parent / (directory.name + "-discover-response.json")
    request.write_text(json.dumps({"operation": "describe", "snapshot": snapshot}))
    process = ManagedProcess(
        [python, "-m", "openbacktesting_studio.execution.worker", str(request), str(response)]
    )
    started = time.monotonic()
    code = process.wait(timeout)
    if not response.is_file() or response.stat().st_size > 8 * 1024 * 1024:
        raise WorkspaceError(
            "DiscoveryFailed",
            "Worker did not return a valid description",
            422,
            stdout=process.stdout.export(),
            stderr=process.stderr.export(),
        )
    result = json.loads(response.read_text())
    result.update(
        stdout=process.stdout.export(),
        stderr=process.stderr.export(),
        elapsed=time.monotonic() - started,
    )
    if code or not result.get("ok"):
        message = result.pop("message", "Strategy discovery failed")
        result["frameworkCode"] = result.pop("code", None)
        raise WorkspaceError("DiscoveryFailed", message, 422, **result)
    return result | {"sourceHash": snapshot["hash"], "sourceFiles": snapshot["files"]}
