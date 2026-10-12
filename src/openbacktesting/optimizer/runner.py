"""Execute and commit trials sequentially; file side effects occur only during explicit execution."""

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
    """Execute or resume a plan; executor receives title-based requests and returns complete Portfolio dictionaries.

    Constraints receive complete wire values; cancel is a no-argument bool callable, and on_progress only consumes notifications.
    Only an explicit experiment_id indicates resumption; failed trials are not retried automatically.
    """
    if (constraint is None) != (plan_value.snapshot()["constraintId"] is None):
        raise ValueError("optimizer: constraint does not match the plan digest")
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
                                raise TypeError("optimizer: constraint must return bool")
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
                    except Exception as error:  # noqa: BLE001 — isolate arbitrary user strategy/export exceptions and record failures
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
                    failure.add_note(f"Failed to persist experiment failure status: {status_error}")
                raise
            finally:
                store.close()
    except Exception as error:
        message = str(error) + " ".join(getattr(error, "__notes__", ()))
        raise OptimizationError(message, path, experiment_id, committed) from error
    return open_result(path, experiment_id)
