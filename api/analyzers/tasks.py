from celery.utils.log import get_logger

from analyzers import summarize
from doc_store import disk_store
from services import persist
from celery import shared_task

logger = get_logger(__name__)


@shared_task(bind=True, trail=True)
def summarize_content(self, hash: str):
    if persist.has_summary(hash):
        logger.info(f"[Summarize] Skipping - Already processed: {hash}")
        return

    task_id = self.request.id
    persist.update_processing_action_state(hash, task_id, "STARTED")
    store = disk_store.default_store(logging_func=logger.info)
    docs = store.restore_document_content(hash)
    if len(docs) == 0:
        logger.info(f"[Summarize] Skipping - No content found: {hash}")
        return

    logger.info(f"[Summarize] Processing size: {len(docs)}")
    summary_text = summarize.summarize_document(docs)

    if summary_text:
        logger.info(f"[Summarize] Saving summary: {hash}")
        persist.save_summary(hash, summary_text)
    else:
        logger.info(f"[Summarize] No summary generated for {hash}")

    persist.update_processing_action_state(hash, task_id, "COMPLETE")
