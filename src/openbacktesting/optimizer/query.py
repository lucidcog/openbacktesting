"""从磁盘标量投影查询实验；不导入策略或重算统计。"""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal

from openbacktesting.optimizer.models import digest, encode
from openbacktesting.optimizer.storage import (
    check_version,
    connect,
    counts,
    load_report,
    local_path,
)


def _compare(left, right):
    a, b = json.loads(left), json.loads(right)
    if a[0] == "number":
        a, b = Decimal(str(a[1])), Decimal(str(b[1]))
    else:
        a, b = a[1], b[1]
    return (a > b) - (a < b)


def _key(value, kind):
    return encode([kind, json.loads(value)]) if value is not None else None


def _status(alias):
    return (
        f"CASE WHEN {alias}.trial IS NULL THEN 'missing' "
        f"ELSE COALESCE({alias}.status, CASE WHEN {alias}.kind='null' THEN 'null' ELSE 'ok' END) END"
    )


def _direction(path):
    return (
        "asc"
        if "drawdown" in path.casefold() and not path.startswith("extensions.legacy.")
        else "desc"
    )


def _limit(value):
    if type(value) is not int or not 1 <= value <= 1000:
        raise ValueError("optimizer: limit 必须在 1..1000")


@dataclass(frozen=True)
class ExperimentResult:
    """可重开的只读结果集句柄；每次访问独立连接，无活策略引用。"""

    path: str
    experiment_id: str

    @contextmanager
    def _connection(self):
        conn = connect(self.path, readonly=True)
        try:
            check_version(conn)
            if conn.execute("SELECT id FROM experiment").fetchone()[0] != self.experiment_id:
                raise ValueError("optimizer: 实验 ID 不匹配")
            conn.create_collation("exact", _compare)
            conn.create_function("scalar_key", 2, _key, deterministic=True)
            conn.execute("PRAGMA temp_store=FILE")
            yield conn
        finally:
            conn.close()

    def info(self) -> dict:
        """返回实验状态、分类计数及不可变计划副本。"""
        with self._connection() as conn:
            return counts(conn) | {
                "plan": json.loads(conn.execute("SELECT plan FROM experiment").fetchone()[0])
            }

    def fields(self) -> list[dict]:
        """返回标量的路径、类型、单位、状态、方法与建议排序方向。"""
        with self._connection() as conn:
            return [
                dict(row) | {"suggestedDirection": _direction(row["path"])}
                for row in conn.execute(
                    "SELECT DISTINCT path,kind,unit,status,method FROM scalars ORDER BY path"
                )
            ]

    def load_portfolio(self, trial_id: str) -> dict:
        """校验并加载单份完整报告，失败或损坏时明确拒绝。"""
        with self._connection() as conn:
            return load_report(conn, trial_id)

    def trials(self, *, limit: int = 100, offset: int = 0) -> list[dict]:
        """分页浏览所有已访问试验的实时状态，不附带完整 Portfolio。"""
        _limit(limit)
        if type(offset) is not int or offset < 0:
            raise ValueError("optimizer: offset 必须为非负整数")
        with self._connection() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT t.id AS trial_id,t.ordinal,t.request,t.state,t.attempt,a.error FROM trials t JOIN attempts a ON a.trial=t.id AND a.number=t.attempt ORDER BY t.ordinal LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            ]

    def query(
        self, *, order_by=(), filters=(), fields=(), limit: int = 100, cursor: str | None = None
    ) -> dict:
        """查询成功组的标量与参数；游标固定提交范围，重新查询刷新。

        order_by 为路径或 (路径, asc/desc)，filters 为 (路径, 运算符, 值)。
        运算符支持 eq/ne/lt/le/gt/ge/status；点号和反斜杠键需反斜杠转义。
        """
        _limit(limit)
        ordering = [
            (item, _direction(item)) if isinstance(item, str) else tuple(item) for item in order_by
        ]
        if any(len(item) != 2 or item[1] not in ("asc", "desc") for item in ordering):
            raise ValueError("optimizer: 非法排序方向")
        operations = {"eq": "=", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}
        if any(len(item) != 3 or item[1] not in (*operations, "status") for item in filters):
            raise ValueError("optimizer: 非法过滤条件")
        paths = list(
            dict.fromkeys([p for p, _ in ordering] + [f[0] for f in filters] + list(fields))
        )
        query_hash = digest([ordering, filters, fields, limit])
        with self._connection() as conn:
            maximum = conn.execute("SELECT sequence FROM experiment").fetchone()[0]
            token = (
                json.loads(cursor)
                if cursor is not None
                else {
                    "experiment": self.experiment_id,
                    "query": query_hash,
                    "watermark": maximum,
                    "offset": 0,
                }
            )
            if (
                not isinstance(token, dict)
                or token.get("experiment") != self.experiment_id
                or token.get("query") != query_hash
                or type(token.get("watermark")) is not int
                or not 0 <= token["watermark"] <= maximum
                or type(token.get("offset")) is not int
                or token["offset"] < 0
            ):
                raise ValueError("optimizer: 游标与查询不匹配")
            joins, selected, params, metadata = [], [], [], {}
            for i, path in enumerate(paths):
                rows = conn.execute(
                    "SELECT DISTINCT kind,unit,method FROM scalars s JOIN trials t ON s.trial=t.id WHERE s.path=? AND t.sequence<=?",
                    (path, token["watermark"]),
                ).fetchall()
                if not rows:
                    raise ValueError(f"optimizer: 未知或非标量字段 {path}")
                signatures = {
                    (r["kind"], r["unit"], r["method"]) for r in rows if r["kind"] != "null"
                }
                if len(signatures) > 1 or len({(r["unit"], r["method"]) for r in rows}) > 1:
                    raise ValueError(f"optimizer: 字段类型或统计口径不一致 {path}")
                metadata[path] = next(iter(signatures), ("null", rows[0]["unit"], rows[0]["method"]))
                joins.append(f"LEFT JOIN scalars s{i} ON s{i}.trial=t.id AND s{i}.path=?")
                params.append(path)
                selected += [f"s{i}.value AS v{i}", f"{_status(f's{i}')} AS z{i}"]
            where = ["t.state='succeeded'", "t.sequence<=?"]
            params.append(token["watermark"])
            for path, op, value in filters:
                alias = f"s{paths.index(path)}"
                if op == "status":
                    where.append(f"{_status(alias)}=?")
                    params.append(value)
                else:
                    kind = metadata[path][0]
                    valid = (
                        kind == "number"
                        and type(value) in (int, float, str)
                        or kind == "string"
                        and type(value) is str
                        or kind == "boolean"
                        and type(value) is bool
                    )
                    if not valid:
                        raise ValueError("optimizer: 过滤值类型不匹配")
                    if kind == "number":
                        number = Decimal(str(value))
                        if not number.is_finite():
                            raise ValueError("optimizer: 非有限过滤值")
                    where.append(
                        f"scalar_key({alias}.value,{alias}.kind) COLLATE exact {operations[op]} ?"
                    )
                    params.append(encode([kind, value]))
            order = []
            for path, direction in ordering:
                alias = f"s{paths.index(path)}"
                order += [
                    f"({alias}.value IS NULL) ASC",
                    f"scalar_key({alias}.value,{alias}.kind) COLLATE exact {direction.upper()}",
                ]
            order.append("t.ordinal ASC")
            columns = "t.id,t.ordinal,t.request" + ("," + ",".join(selected) if selected else "")
            sql = f"SELECT {columns} FROM trials t {' '.join(joins)} WHERE {' AND '.join(where)} ORDER BY {','.join(order)} LIMIT ? OFFSET ?"
            rows = conn.execute(sql, (*params, limit + 1, token["offset"])).fetchall()
            result = [
                {
                    "trial_id": row["id"],
                    "ordinal": row["ordinal"],
                    "inputs": json.loads(row["request"])["values"],
                    "values": {
                        p: {
                            "value": json.loads(row[f"v{i}"]) if row[f"v{i}"] is not None else None,
                            "status": row[f"z{i}"],
                            "unit": metadata[p][1],
                            "methodId": metadata[p][2],
                        }
                        for i, p in enumerate(paths)
                    },
                }
                for row in rows[:limit]
            ]
            following = (
                encode(token | {"offset": token["offset"] + limit}) if len(rows) > limit else None
            )
            return {"rows": result, "cursor": following, "watermark": token["watermark"]}

    def backup(self, destination) -> str:
        """一致性备份到新本地文件，拒绝覆盖已有文件。"""
        target = local_path(destination)
        with target.open("xb"):
            pass
        try:
            with self._connection() as source:
                dest = sqlite3.connect(target)
                try:
                    source.backup(dest)
                finally:
                    dest.close()
        except BaseException:
            target.unlink()
            raise
        return str(target)


def open_result(path, experiment_id: str | None = None) -> ExperimentResult:
    """只读打开一个实验结果库，无策略或行情依赖。"""
    conn = connect(path, readonly=True)
    try:
        check_version(conn)
        current = conn.execute("SELECT id FROM experiment").fetchone()[0]
        if experiment_id is not None and current != experiment_id:
            raise ValueError("optimizer: 实验 ID 不匹配")
        return ExperimentResult(str(local_path(path)), current)
    finally:
        conn.close()
