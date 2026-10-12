"""Local single-experiment SQLite result database; one report corresponds to one atomic commit."""

import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from openbacktesting.optimizer.models import encode
from openbacktesting.optimizer.validation import validate_report

APPLICATION_ID = 1128546128
VERSION = 1
DDL = """
CREATE TABLE experiment(id TEXT PRIMARY KEY, plan TEXT NOT NULL, status TEXT NOT NULL,
                       sequence INTEGER NOT NULL DEFAULT 0);
CREATE TABLE trials(id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE NOT NULL,
 request TEXT NOT NULL UNIQUE, state TEXT NOT NULL, attempt INTEGER NOT NULL,
 sequence INTEGER UNIQUE, report TEXT, hash TEXT);
CREATE TABLE attempts(trial TEXT NOT NULL REFERENCES trials(id), number INTEGER NOT NULL,
 state TEXT NOT NULL, started TEXT NOT NULL, ended TEXT, error TEXT,
 PRIMARY KEY(trial,number));
CREATE TABLE scalars(trial TEXT NOT NULL REFERENCES trials(id), path TEXT NOT NULL,
 value TEXT, kind TEXT NOT NULL, unit TEXT, status TEXT, method TEXT,
 PRIMARY KEY(trial,path));
CREATE INDEX scalar_path ON scalars(path);
"""


def local_path(path):
    raw = str(path)
    if raw.startswith(("file:", "//", "\\\\")) or raw == ":memory:":
        raise ValueError("optimizer: a local file path is required")
    return Path(path).expanduser().resolve()


def connect(path, *, readonly=False):
    path = local_path(path)
    conn = sqlite3.connect(
        path.as_uri() + ("?mode=ro" if readonly else "?mode=rwc"), uri=True, timeout=1
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    if readonly:
        conn.execute("PRAGMA query_only=ON")
    return conn


def check_version(conn):
    if (
        conn.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
        or conn.execute("PRAGMA user_version").fetchone()[0] != VERSION
    ):
        raise ValueError("optimizer: unsupported result database version")


@contextmanager
def owner(path):
    """Separate lock database holding an operating-system file lock without blocking result database readers."""
    path = local_path(path)
    lock = sqlite3.connect(str(path) + ".owner", timeout=0)
    try:
        lock.execute("BEGIN EXCLUSIVE")
        yield path
    finally:
        lock.close()


def now():
    return datetime.now(UTC).isoformat()


def flatten(value, path="", metadata=None):
    """Scalar projection; escape dots/backslashes in keys with a backslash, and do not traverse arrays."""
    if isinstance(value, dict):
        if {"value", "unit", "status", "methodId"} <= value.keys():
            metadata = value
        elif value.get("kind") in ("aware", "naive") and "value" in value:
            metadata = {"unit": "ns"}
        for key, child in value.items():
            part = key.replace("\\", "\\\\").replace(".", "\\.")
            yield from flatten(
                child, f"{path}.{part}" if path else part, metadata if key == "value" else None
            )
    elif not isinstance(value, list):
        meta = metadata or {}
        if path.casefold().endswith(("durationns", ".ns")):
            meta = meta | {"unit": "ns"}
        kind = {str: "string", int: "number", float: "number", bool: "boolean", type(None): "null"}[
            type(value)
        ]
        if (
            isinstance(value, str)
            and re.fullmatch(r"-?\d+", value)
            and (metadata is not None or meta.get("unit") == "ns")
        ):
            kind = "number"
        yield (
            path,
            None if value is None else encode(value),
            kind,
            meta.get("unit"),
            meta.get("status"),
            meta.get("methodId"),
        )


class Store:
    def __init__(self, path, plan_value, *, experiment_id=None):
        self.path = local_path(path)
        self.conn = connect(path)
        try:
            if experiment_id is None:
                if self.conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchone():
                    raise FileExistsError("optimizer: database already contains an experiment; resume explicitly or use a new path")
                self.conn.executescript(DDL)
                self.conn.execute(f"PRAGMA application_id={APPLICATION_ID}")
                self.conn.execute(f"PRAGMA user_version={VERSION}")
                self.id = uuid4().hex
                self.conn.execute(
                    "INSERT INTO experiment(id,plan,status) VALUES(?,?,'running')",
                    (self.id, plan_value._json),
                )
                self.conn.commit()
            else:
                check_version(self.conn)
                row = self.conn.execute(
                    "SELECT * FROM experiment WHERE id=?", (experiment_id,)
                ).fetchone()
                if row is None or row["plan"] != plan_value._json:
                    raise ValueError("optimizer: experiment identity or plan does not match")
                self.id = experiment_id
            mode = self.conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            self.conn.execute("PRAGMA synchronous=FULL")
            if mode != "wal" or self.conn.execute("PRAGMA synchronous").fetchone()[0] != 2:
                raise RuntimeError("optimizer: unable to enable local durability policy")
            with self.conn:
                self.conn.execute(
                    "UPDATE attempts SET state='interrupted',ended=? WHERE state IN ('running','persisting')",
                    (now(),),
                )
                self.conn.execute(
                    "UPDATE trials SET state='interrupted' WHERE state IN ('running','persisting')"
                )
                self.conn.execute("UPDATE experiment SET status='running'")
        except BaseException:
            self.conn.close()
            raise

    def close(self):
        self.conn.close()

    def start(self, ordinal, request):
        trial_id = f"{self.id}:{ordinal}"
        row = self.conn.execute("SELECT * FROM trials WHERE id=?", (trial_id,)).fetchone()
        if row and row["state"] in ("succeeded", "failed", "skipped_constraint"):
            return None
        attempt = row["attempt"] + 1 if row else 1
        with self.conn:
            self.conn.execute(
                "INSERT INTO trials(id,ordinal,request,state,attempt) VALUES(?,?,?,'running',?) ON CONFLICT(id) DO UPDATE SET state='running',attempt=excluded.attempt",
                (trial_id, ordinal, encode(request), attempt),
            )
            self.conn.execute(
                "INSERT INTO attempts(trial,number,state,started) VALUES(?,?,'running',?)",
                (trial_id, attempt, now()),
            )
        return trial_id, attempt

    def state(self, trial_id, attempt, state, error=None):
        with self.conn:
            count = self.conn.execute(
                "UPDATE trials SET state=? WHERE id=? AND attempt=? AND state IN ('running','persisting')",
                (state, trial_id, attempt),
            ).rowcount
            if count != 1:
                raise ValueError("optimizer: stale trial attempt")
            self.conn.execute(
                "UPDATE attempts SET state=?,ended=?,error=? WHERE trial=? AND number=?",
                (state, None if state == "persisting" else now(), error, trial_id, attempt),
            )

    def commit(self, trial_id, attempt, report):
        validate_report(report)
        payload = encode(report)
        checksum = hashlib.sha256(payload.encode()).hexdigest()
        row = self.conn.execute("SELECT * FROM trials WHERE id=?", (trial_id,)).fetchone()
        if row is None or row["attempt"] != attempt:
            raise ValueError("optimizer: stale trial attempt")
        if row["state"] == "succeeded":
            if row["hash"] != checksum:
                raise ValueError("optimizer: committed report content conflicts")
            return
        if row["state"] != "persisting":
            raise ValueError("optimizer: trial has not produced a complete report")
        request = json.loads(row["request"])
        inputs = report["context"]["inputs"]
        if inputs is None or any(inputs.get(k) != v for k, v in request.items()):
            raise ValueError("optimizer: Portfolio parameters do not match the trial")
        execution = json.loads(self.conn.execute("SELECT plan FROM experiment").fetchone()[0])[
            "execution"
        ]
        expected = execution.get("backtest")
        if expected is not None:
            actual = report["context"]["backtest"]
            if actual is None or any(actual.get(k) != v for k, v in expected.items()):
                raise ValueError("optimizer: Portfolio configuration does not match the experiment")
        with self.conn:
            self.conn.execute("UPDATE experiment SET sequence=sequence+1")
            sequence = self.conn.execute("SELECT sequence FROM experiment").fetchone()[0]
            self.conn.execute(
                "UPDATE trials SET state='succeeded',sequence=?,report=?,hash=? WHERE id=?",
                (sequence, payload, checksum, trial_id),
            )
            self.conn.executemany(
                "INSERT INTO scalars VALUES(?,?,?,?,?,?,?)",
                ((trial_id, *item) for item in flatten(report)),
            )
            self.conn.execute(
                "UPDATE attempts SET state='succeeded',ended=? WHERE trial=? AND number=?",
                (now(), trial_id, attempt),
            )

    def finish(self, state):
        with self.conn:
            self.conn.execute("UPDATE experiment SET status=?", (state,))


def load_report(conn, trial_id):
    row = conn.execute("SELECT report,hash,state FROM trials WHERE id=?", (trial_id,)).fetchone()
    if row is None or row["state"] != "succeeded":
        raise ValueError("optimizer: this trial has no committed Portfolio")
    if hashlib.sha256(row["report"].encode()).hexdigest() != row["hash"]:
        raise ValueError("optimizer: Portfolio content verification failed")
    return validate_report(json.loads(row["report"]))


def counts(conn):
    experiment = conn.execute("SELECT * FROM experiment").fetchone()
    states = dict(conn.execute("SELECT state,COUNT(*) FROM trials GROUP BY state").fetchall())
    total = json.loads(experiment["plan"])["total"]
    committed = states.get("succeeded", 0)
    skipped = states.get("skipped_constraint", 0)
    failed = states.get("failed", 0)
    return {
        "experiment_id": experiment["id"],
        "status": experiment["status"],
        "total": total,
        "checked": sum(states.values()),
        "committed": committed,
        "skipped": skipped,
        "failed": failed,
        "running": states.get("running", 0),
        "computed": committed + states.get("persisting", 0),
        "remaining": total - committed - skipped - failed,
    }
