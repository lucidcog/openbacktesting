"""Bounded, read-only verification runs with explicit failure and evidence semantics."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from check_package import project_files

LOG_LIMIT = 1024 * 1024


@dataclass(frozen=True)
class Check:
    id: str
    argv: tuple[str, ...]
    profiles: tuple[str, ...] = ("full",)
    phase: str = "check"
    needs: tuple[str, ...] = ()
    cwd: str = "."
    timeout: float = 600
    remedy: str = "Inspect the recorded command and diagnostics, fix the cause, and rerun."
    maintenance: bool = False


def redact(text):
    """Remove whole credential values, including JSON and startup URL forms."""
    text = re.sub(r"(?im)((?:set-cookie|cookie|authorization)\s*:[^\S\n]*)[^\r\n]+", r"\1[REDACTED]", text)
    text = re.sub(
        r'''(?ix)((?:["']?)(?:startup[_-]?token|access[_-]?token|token|csrf|x-studio-csrf|password|secret|cookie|set-cookie|authorization)(?:["']?)\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s&,;}]+)''',
        r"\1[REDACTED]", text,
    )
    return text


def stamp():
    return datetime.now(timezone.utc).isoformat()


def git(root, *args):
    result = subprocess.run(["git", "--no-optional-locks", *args], cwd=root, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def snapshot(root):
    result = {}
    for path in project_files(root):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[name] = "symlink:" + os.readlink(path)
        else:
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def tool_version(command, root):
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
        return redact((result.stdout or result.stderr).strip())[:500]
    except (OSError, subprocess.TimeoutExpired) as error:
        return str(error)


def select(checks, profile):
    if profile not in {"docs", "core", "studio", "full"}:
        raise ValueError(f"Unknown profile: {profile}")
    chosen = [c for c in checks if profile == "full" or profile in c.profiles]
    ordered, active, done = [], set(), set()
    by_id = {c.id: c for c in checks}
    if len(by_id) != len(checks):
        raise ValueError("Duplicate check ID")

    def visit(check):
        if check.id in done:
            return
        if check.id in active:
            raise ValueError(f"Cyclic dependency: {check.id}")
        active.add(check.id)
        for name in check.needs:
            if name not in by_id:
                raise ValueError(f"Missing check dependency: {name}")
            visit(by_id[name])
        active.remove(check.id)
        done.add(check.id)
        ordered.append(check)

    for check in chosen:
        visit(check)
    return ordered


def stop_group(process):
    """Reap the leader and stop descendants even if the leader already exited."""
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def execute(check, root, directory, env=None):
    started = time.monotonic()
    row = {"id": check.id, "phase": check.phase, "argv": [redact(a) for a in check.argv],
           "cwd": check.cwd, "status": "error", "exitCode": None, "durationMs": 0,
           "reason": None, "remedy": check.remedy, "evidence": [], "truncated": False}
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    counts = {"stdout": 0, "stderr": 0}
    threads = []
    process = None

    def drain(name, stream):
        try:
            while chunk := stream.read(4096):
                counts[name] += len(chunk)
                available = max(0, LOG_LIMIT - len(buffers[name]))
                buffers[name].extend(chunk[:available])
        finally:
            stream.close()

    try:
        cwd = (root / check.cwd).resolve()
        if not cwd.is_relative_to(root.resolve()):
            raise ValueError("Check working directory escapes repository")
        process = subprocess.Popen(check.argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=os.name == "posix")
        for name in buffers:
            thread = threading.Thread(target=drain, args=(name, getattr(process, name)), daemon=True)
            thread.start()
            threads.append(thread)
        process.wait(timeout=check.timeout)
        row["exitCode"] = process.returncode
        row["status"] = "passed" if process.returncode == 0 else "failed"
        if process.returncode:
            row["reason"] = f"Command exited with {process.returncode}"
    except subprocess.TimeoutExpired:
        row.update(status="error", reason=f"Timed out after {check.timeout:g}s")
    except KeyboardInterrupt:
        row.update(status="cancelled", reason="Verification interrupted")
    except (OSError, ValueError) as error:
        row.update(status="error", reason=redact(str(error)))
    finally:
        if process is not None:
            stop_group(process)
        for thread in threads:
            thread.join(timeout=5)
        for name, data in buffers.items():
            truncated = counts[name] > len(data)
            value = redact(data.decode("utf-8", errors="replace"))
            if truncated:
                value += "\n[OUTPUT TRUNCATED]\n"
            path = directory / f"{check.id}.{name}.log"
            path.write_text(value)
            row["evidence"].append(path.name)
            row["truncated"] |= truncated
        row["durationMs"] = round((time.monotonic() - started) * 1000)
    return row


def run_checks(root, checks, profile, *, output_root=None, protect=True, env=None):
    root = Path(root).resolve()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    directory = (output_root or root / ".verification/harness") / run_id
    directory.mkdir(parents=True, exist_ok=False)
    before = snapshot(root) if protect else {}
    environment = os.environ.copy() if env is None else dict(env)
    environment["HARNESS_EVIDENCE_DIR"] = str(directory)
    report = {"schemaVersion": 1, "runId": run_id, "profile": profile,
              "commit": git(root, "rev-parse", "HEAD"),
              "dirty": bool(git(root, "status", "--porcelain")),
              "platform": platform.platform(), "python": platform.python_version(),
              "tools": {"uv": tool_version(["uv", "--version"], root)},
              "lockDigests": {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                              for p in ("uv.lock", "studio/uv.lock", "studio/web/package-lock.json")
                              if (root / p).exists()},
              "selectedChecks": [check.id for check in checks],
              "interpreters": {"runner": platform.python_version(), "requested": environment.get("HARNESS_PYTHON", platform.python_version())},
              "startedAt": stamp(), "finishedAt": None, "status": "error", "checks": [],
              "excludedChecks": [] if environment.get("OPENBACKTESTING_RUN_SLOW_EXAMPLES") == "1"
              else [{"id": "slow-ml-examples", "reason": "Enable OPENBACKTESTING_RUN_SLOW_EXAMPLES=1 explicitly."}]}
    if profile in {"studio", "full", "maintenance"}:
        report["tools"].update({tool: tool_version([tool, "--version"], root) for tool in ("node", "npm")})

    def save():
        target = directory / "result.json"
        temporary = directory / "result.tmp"
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        temporary.replace(target)

    save()
    cancelled = False
    for check in checks:
        statuses = {row["id"]: row["status"] for row in report["checks"]}
        failed = [name for name in check.needs if statuses.get(name) != "passed"]
        if cancelled or failed:
            row = {"id": check.id, "phase": check.phase, "argv": [redact(a) for a in check.argv], "cwd": check.cwd,
                   "status": "cancelled" if cancelled else "blocked", "durationMs": 0, "exitCode": None,
                   "reason": "Run cancelled" if cancelled else "Dependencies did not pass: " + ", ".join(failed),
                   "remedy": check.remedy, "evidence": [], "truncated": False}
        else:
            print(f"[{profile}] {check.id}", flush=True)
            row = execute(check, root, directory, environment)
            cancelled = row["status"] == "cancelled"
        report["checks"].append(row)
        if check.id in {"root-env", "studio-env"} and row["status"] == "passed":
            executable = root / (".venv/bin/python" if check.id == "root-env" else "studio/.venv/bin/python")
            report["interpreters"][check.id] = tool_version([str(executable), "--version"], root)
        save()
    if protect:
        after = snapshot(root)
        changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        report["checks"].append({"id": "source-integrity", "phase": "integrity", "argv": [], "cwd": ".",
                                 "status": "failed" if changed else "passed", "durationMs": 0, "exitCode": 1 if changed else 0,
                                 "reason": "Protected files changed; inspect without resetting user edits" if changed else None,
                                 "files": changed, "evidence": [], "remedy": "Move outputs to ignored directories; review the changes."})
    report["status"] = "passed" if report["checks"] and all(r["status"] == "passed" for r in report["checks"]) else "cancelled" if cancelled else "failed"
    report["finishedAt"] = stamp()
    save()
    summary = [f"# Verification {report['status']}", "", f"Run: `{run_id}`; profile: `{profile}`", ""]
    summary += [f"- {r['id']}: **{r['status']}** ({r['durationMs']} ms)" + (f" — {r['reason']}" if r.get('reason') else "") for r in report["checks"]]
    (directory / "summary.md").write_text("\n".join(summary) + "\n")
    print(f"{report['status']}: {directory / 'result.json'}", flush=True)
    return report, directory
