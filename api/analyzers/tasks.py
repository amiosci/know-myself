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
    run_analyzer: Callable[[list[Document]], T],
    on_generated: Callable[[str, T], None],
):
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
    summary_text = run_analyzer(docs)

    if summary_text:
        logger.info(f"[{task_name}] Saving: {hash}")
        on_generated(hash, summary_text)
    else:
        logger.info(f"[{task_name}] Nothing generated for {hash}")

    persist.update_processing_action_state(hash, task_id, task_name, "COMPLETE")


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
