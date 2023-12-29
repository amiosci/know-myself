import asyncio

from celery import shared_task
from celery.utils.log import get_logger
from doc_store import disk_store
from services import persist

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

    async def run_processor():
        persist.update_processing_action_state(hash, task_id, task_name, "STARTED")
        task_processor = task_processor_ctor()
        task_result = await task_processor.process_context(task_context)
        if task_result.result_type == TaskResultType.SKIPPED:
            logger.info(f"[{task_name}] Skipping - Already processed: {hash}")

        terminal_status = "FAILED"
        if task_result.result_type == TaskResultType.PROCESSED:
            terminal_status = "COMPLETE"
        persist.update_processing_action_state(
            hash, task_id, task_name, terminal_status
        )

    async def process_with_timeout():
        async with asyncio.timeout(3600):  # 1h
            return await run_processor()

    try:
        asyncio.run(process_with_timeout())
    except (TimeoutError, asyncio.CancelledError) as e:
        status = "CANCELLED"
        if isinstance(e, TimeoutError):
            status = "TIMEOUT"
        persist.update_processing_action_state(hash, task_id, task_name, status)
    except:
        persist.update_processing_action_state(hash, task_id, task_name, "FAILED")


@shared_task(bind=True, trail=True)
def summarize_content(self, hash: str, url: str):
    _run_celery_analyzer_task(
        Context(hash=hash, url=url),
        self.request.id,
        "Summarize",
        SummarizeContent,
    )


@shared_task(bind=True, trail=True)
def extract_entity_relations(self, hash: str, url: str):
    _run_celery_analyzer_task(
        Context(hash=hash, url=url),
        self.request.id,
        "Extract Relations",
        ExtractContentRelations,
    )
