"""串行逐组执行与提交；文件副作用只在显式执行时发生。"""

import sqlite3

from openbacktesting.optimizer.models import OptimizationError, _ExportError
from openbacktesting.optimizer.plan import combinations
from openbacktesting.optimizer.query import open_result
from openbacktesting.optimizer.storage import Store, counts, owner
from openbacktesting.optimizer.validation import validate_report


def execute(
    plan_value,
    executor,
    path,
    *,
    experiment_id=None,
    constraint=None,
    cancel=None,
    on_progress=None,
):
    """执行或恢复计划；executor 接收标题请求并返回完整 Portfolio 字典。

    约束接收完整 wire 值，cancel 是无参 bool callable；on_progress 只消费通知。
    仅显式 experiment_id 表示恢复；失败组不自动重试。
    """
    if (constraint is None) != (plan_value.snapshot()["constraintId"] is None):
        raise ValueError("optimizer: constraint 与计划摘要不匹配")
    committed = 0
    store = None
    try:
        with owner(path):
            store = Store(path, plan_value, experiment_id=experiment_id)
            experiment_id = store.id
            try:
                committed = counts(store.conn)["committed"]
                for ordinal, request in combinations(plan_value):
                    if cancel is not None and cancel():
                        store.finish("cancelled")
                        break
                    attempt = store.start(ordinal, request)
                    if attempt is None:
                        continue
                    trial_id, number = attempt
                    if constraint is not None:
                        try:
                            accepted = constraint(dict(request["values"]))
                            if type(accepted) is not bool:
                                raise TypeError("optimizer: 约束必须返回 bool")
                        except Exception as error:
                            store.state(
                                trial_id,
                                number,
                                "failed",
                                f"constraint: {type(error).__name__}: {str(error)[:2000]}",
                            )
                            raise
                        if not accepted:
                            store.state(trial_id, number, "skipped_constraint", "constraint_false")
                            continue
                    phase = "execution"
                    try:
                        report = executor(request)
                        phase = "export"
                        validate_report(report)
                    except Exception as error:  # noqa: BLE001 — 隔离任意用户策略/导出异常并记录失败
                        store.state(
                            trial_id,
                            number,
                            "failed",
                            f"{'export' if isinstance(error, _ExportError) else phase}: {type(error).__name__}: {str(error)[:2000]}",
                        )
                    else:
                        store.state(trial_id, number, "persisting")
                        store.commit(trial_id, number, report)
                        del report
                        committed += 1
                        if on_progress is not None:
                            on_progress(
                                counts(store.conn)
                                | {"event": "trial_committed", "trial_id": trial_id}
                            )
                else:
                    store.finish(
                        "completed_with_errors" if counts(store.conn)["failed"] else "completed"
                    )
            except BaseException as failure:
                try:
                    store.finish("failed")
                except sqlite3.Error as status_error:
                    failure.add_note(f"实验失败状态未能写盘: {status_error}")
                raise
            finally:
                store.close()
    except Exception as error:
        message = str(error) + " ".join(getattr(error, "__notes__", ()))
        raise OptimizationError(message, path, experiment_id, committed) from error
    return open_result(path, experiment_id)
