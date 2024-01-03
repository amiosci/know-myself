from celery.utils.log import get_logger

from utilities import create_app
import celery.signals
import datetime
import time

from services.persist import metrics

from analyzers import tasks as analyzer_tasks
import flask_celery

app = create_app().extensions["celery"]
logger = get_logger(__name__)


# register celery signals
@celery.signals.task_prerun.connect
def celery_task_prerun(task, **kwargs):
    task.start_time = time.time()


@celery.signals.task_postrun.connect
def celery_task_postrun(task_id, state, task, **kwargs):
    runtime = time.time() - task.start_time

    # not working for now ...
    parent_id = None

    logger.info(f"[Saving Metrics]: {task_id}")
    # save metrics
    metrics.report_task_metrics(
        task_id,
        parent_id,
        metrics.TaskMetric(
            result=state,
            duration_seconds=runtime,
            started_at=datetime.datetime.fromtimestamp(task.start_time),
        ),
    )


if __name__ == "__main__":
    args = ["worker", "--loglevel=INFO", "--concurrency=1"]
    app.worker_main(argv=args)
