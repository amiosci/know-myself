from functools import partial
from typing import Callable

from celery import shared_task, group
from celery.canvas import Signature

from analyzers import tasks as analyzer_tasks
from services.persist import task
import constants


def _register_task(
    hash: str,
    force_process: bool,
    parent_task_id: str,
    task_name: str,
    task_func: Callable[[str, bool], Signature],
    requested_task_name: str | None = None,
) -> Signature | None:
    if requested_task_name is not None:
        if requested_task_name != task_name:
            print(f"Skipping [{task_name}] for requested [{requested_task_name}]")
            return None

    task.create_processing_action(
        hash,
        parent_task_id,
        task_name,
    )

    return task_func(hash, force_process)


@shared_task(bind=True, trail=True)
def process_content(self, hash: str, requested_task_name: str | None = None):
    # map must remain within a celery annotated function, else ampq failures will occur
    task_name_map = {
        constants.SUMMARY_TASK: analyzer_tasks.summarize_content.si,
        constants.ENTITIES_TASK: analyzer_tasks.extract_entity_relations.si,
    }
    task_requests = []
    if requested_task_name is None:
        task_requests.extend(list(map(tuple, task_name_map.items())))
    else:
        requested_task = task_name_map.get(requested_task_name)
        if requested_task is None:
            print(f"No task with found with name: [{requested_task_name}]")
            return
        task_requests.append((requested_task_name, requested_task))
    force_process = requested_task_name is not None
    register_task = partial(
        _register_task,
        hash,
        force_process,
        self.request.id,
        requested_task_name=requested_task_name,
    )

    if not task_requests:
        print("No tasks requested")
        return

    tasks = []
    for name, task_func in task_requests:
        requested_task = register_task(name, task_func)
        if requested_task is None:
            print(f"Task creation failed for {name}")
            continue
        tasks.append(requested_task)

    if not tasks:
        print("No tasks created")
        return
    group(tasks).apply_async()
