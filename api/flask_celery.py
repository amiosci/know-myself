from celery import shared_task, group
from celery.canvas import Signature
from celery.utils.log import get_logger

from typing import Callable, Any
from analyzers import tasks as analyzer_tasks
from services import persist

logger = get_logger(__name__)


def _register_task(
    hash: str,
    parent_task_id: str,
    task_name: str,
    task_func: Callable[[str], Signature],
) -> Signature:
    persist.create_processing_action(
        hash,
        parent_task_id,
        task_name,
    )

    return task_func(hash)


@shared_task(bind=True, trail=True)
def process_content(self, hash: str):
    print(self.request.id)
    # register all tasks to run in group
    tasks = []
    tasks.append(
        _register_task(
            hash,
            self.request.id,
            "Summarize",
            analyzer_tasks.summarize_content.si,  # type: ignore
        )
    )
    tasks.append(
        _register_task(
            hash,
            self.request.id,
            "Extract Relations",
            analyzer_tasks.extract_entity_relations.si,  # type: ignore
        )
    )

    group(tasks).apply_async()
