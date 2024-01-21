import dataclasses
import datetime

from services.persist.utils import get_connection


@dataclasses.dataclass
class TaskMetric:
    result: str
    duration_seconds: float
    started_at: datetime.datetime


def report_task_metrics(task_id: str, metrics: TaskMetric):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO genai_ops.process_task_metrics (task_id, result, started_at, duration) "
                "VALUES (%s, %s, %s, %s)",
                (
                    (
                        task_id,
                        metrics.result,
                        metrics.started_at,
                        metrics.duration_seconds,
                    )
                ),
            )
