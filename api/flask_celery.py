from functools import partial
from typing import Callable

from celery import shared_task, group
from celery.canvas import Signature

from analyzers import tasks as analyzer_tasks
from services.persist import task
import constants


def _register_task(
    hash: str,
    parent_task_id: str,
    task_name: str,
    task_func: Callable[[str], Signature],
) -> Signature:
    task.create_processing_action(
        hash,
        parent_task_id,
        task_name,
    )

    return task_func(hash)


@shared_task(bind=True, trail=True)
def process_content(self, hash: str):
    tasks = []
    register_task = partial(_register_task, hash, self.request.id)
    tasks.append(
        register_task(
            constants.SUMMARY_TASK,
            analyzer_tasks.summarize_content.si,  # type: ignore
        )
    )
    tasks.append(
        register_task(
            constants.ENTITIES_TASK,
            analyzer_tasks.extract_entity_relations.si,  # type: ignore
        )
    )

    group(tasks).apply_async()
