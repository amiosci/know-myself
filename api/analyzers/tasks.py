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


def _run_celery_analyzer_task(
    task_context: Context,
    task_id: str,
    task_name: str,
    task_processor_ctor: type[ProcessorBase],
):
    hash = task_context.hash

    with task.assign_processing_action(hash, task_name, task_id) as updater:

        async def run_processor():
            task_processor = task_processor_ctor()
            task_result = await task_processor.process_context(task_context)
            if task_result.result_type == TaskResultType.SKIPPED:
                logger.info(f"[{task_name}] Skipping - Already processed: {hash}")

            terminal_status = "FAILED"
            if task_result.result_type == TaskResultType.PROCESSED:
                terminal_status = "COMPLETE"

            updater.set_status(terminal_status)

        async def process_with_timeout():
            async with asyncio.timeout(3600):  # 1h
                return await run_processor()

        try:
            asyncio.run(process_with_timeout())
        except TimeoutError:
            updater.set_status("TIMEOUT")
        except asyncio.CancelledError:
            updater.set_status("CANCELLED")


@shared_task(bind=True, trail=True)
def summarize_content(self, hash: str):
    _run_celery_analyzer_task(
        Context(hash=hash),
        self.request.id,
        constants.SUMMARY_TASK,
        SummarizeContent,
    )


@shared_task(bind=True, trail=True)
def extract_entity_relations(self, hash: str):
    _run_celery_analyzer_task(
        Context(hash=hash),
        self.request.id,
        constants.ENTITIES_TASK,
        ExtractContentRelations,
    )
