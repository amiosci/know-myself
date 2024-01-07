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
    requested_task_name: str | None = None,
) -> Signature | None:
    if requested_task_name is not None:
        if requested_task_name is not task_name:
            return None

    task.create_processing_action(
        hash,
        parent_task_id,
        task_name,
    )

    return task_func(hash)


@shared_task(bind=True, trail=True)
def process_content(self, hash: str, task_name: str | None = None):
    tasks = []
    register_task = partial(
        _register_task, hash, self.request.id, requested_task_name=task_name
    )

    summarize_task = register_task(
        constants.SUMMARY_TASK,
        analyzer_tasks.summarize_content.si,  # type: ignore
    )
    if summarize_task is not None:
        tasks.append(summarize_task)

    extract_entities_task = register_task(
        constants.ENTITIES_TASK,
        analyzer_tasks.extract_entity_relations.si,  # type: ignore
    )
    if extract_entities_task is not None:
        tasks.append(extract_entities_task)

    if len(tasks) == 0:
        print("No tasks requested")
        return
    group(tasks).apply_async()
