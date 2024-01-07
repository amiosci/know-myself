import asyncio

from celery import shared_task
from celery.utils.log import get_logger
from services.persist import task
import constants

from content_workflow import (
    SummarizeContent,
    ExtractContentRelations,
    Context,
    TaskResultType,
    ProcessorBase,
)

from typing import TypeVar

logger = get_logger(__name__)

T = TypeVar("T")


def _result_type_to_status(result_type: TaskResultType) -> task.ProcessTaskStatus:
    match result_type:
        case TaskResultType.SKIPPED:
            return task.ProcessTaskStatus.SKIPPED
        case TaskResultType.FAILED:
            return task.ProcessTaskStatus.FAILED
        case TaskResultType.PROCESSED:
            return task.ProcessTaskStatus.COMPLETE

    raise ValueError(f"Unexpected TaskResultType {result_type}")


def _run_celery_analyzer_task(
    task_context: Context,
    task_id: str,
    task_name: str,
    task_processor_ctor: type[ProcessorBase],
):
    logger.info(task_context)
    hash = task_context.hash

    with task.assign_processing_action(hash, task_name, task_id) as updater:

        async def run_processor():
            task_processor = task_processor_ctor()
            task_result = await task_processor.process_context(task_context)
            if task_result.result_type == TaskResultType.SKIPPED:
                logger.info(f"[{task_name}] Skipping - Already processed: {hash}")

            logger.info(task_result)
            updater.set_result(
                task.TaskResult(
                    status=_result_type_to_status(task_result.result_type),
                    message=task_result.message,
                )
            )

        async def process_with_timeout():
            async with asyncio.timeout(3600):  # 1h
                return await run_processor()

        try:
            asyncio.run(process_with_timeout())
        except TimeoutError:
            updater.set_result(
                task.TaskResult(
                    status=task.ProcessTaskStatus.TIMEOUT,
                    message="Task timeout after 1h",
                )
            )
        except asyncio.CancelledError:
            updater.set_result(
                task.TaskResult(
                    status=task.ProcessTaskStatus.CANCELLED,
                    message="Task cancellation requested",
                )
            )


@shared_task(bind=True, trail=True, task_track_started=True)
def summarize_content(self, hash: str, force_process: bool):
    _run_celery_analyzer_task(
        Context(hash=hash, force_process=force_process),
        self.request.id,
        constants.SUMMARY_TASK,
        SummarizeContent,
    )


@shared_task(bind=True, trail=True, task_track_started=True)
def extract_entity_relations(self, hash: str, force_process: bool):
    _run_celery_analyzer_task(
        Context(hash=hash, force_process=force_process),
        self.request.id,
        constants.ENTITIES_TASK,
        ExtractContentRelations,
    )
