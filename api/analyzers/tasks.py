import asyncio
from collections.abc import Awaitable

from celery import shared_task
from celery.utils.log import get_logger
from langchain.docstore.document import Document

from analyzers import summarize, extraction
from doc_store import disk_store
from services import persist

from typing import Callable, TypeVar

logger = get_logger(__name__)

T = TypeVar("T")


def _run_celery_analyzer_task(
    hash: str,
    task_id: str,
    task_name: str,
    precondition: Callable[[str], bool],
    run_analyzer: Callable[[list[Document]], Awaitable[T]],
    on_generated: Callable[[str, T], None],
):
    async def run_processor():
        if precondition(hash):
            logger.info(f"[{task_name}] Skipping - Already processed: {hash}")
            return

        persist.update_processing_action_state(hash, task_id, task_name, "STARTED")
        store = disk_store.default_store(logging_func=logger.info)
        docs = store.restore_document_content(hash)
        if len(docs) == 0:
            logger.info(f"[{task_name}] Skipping - No content found: {hash}")
            return

        logger.info(f"[{task_name}] Document size: {len(docs)}")
        analyzer_response = await run_analyzer(docs)

        if analyzer_response:
            logger.info(f"[{task_name}] Saving: {hash}")
            on_generated(hash, analyzer_response)
        else:
            logger.info(f"[{task_name}] Nothing generated for {hash}")

        persist.update_processing_action_state(hash, task_id, task_name, "COMPLETE")
    
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
def summarize_content(self, hash: str):
    _run_celery_analyzer_task(
        hash,
        self.request.id,
        "Summarize",
        persist.has_summary,
        summarize.summarize_document,
        persist.save_summary,
    )


@shared_task(bind=True, trail=True)
def extract_entity_relations(self, hash: str):
    store = disk_store.default_store(logging_func=logger.info)

    _run_celery_analyzer_task(
        hash,
        self.request.id,
        "Extract Relations",
        store.has_entity_relations,
        extraction.extract_entity_relations,
        store.save_entity_relations,
    )
