from celery import shared_task, group
from celery.utils.log import get_logger

from analyzers import tasks as analyzer_tasks
from doc_store import disk_store
from doc_store import doc_loader

logger = get_logger(__name__)


@shared_task(trail=True)
def process_content(hash: str, url: str):
    logger.info(f"[Flask Shim] Processing started for {url}")

    store = disk_store.default_store(logging_func=logger.info)

    if store.has_document_content(hash):
        logger.info(f"[Flask Shim] Skipping - Document content already exists: {hash}")
    else:
        logger.info(f"[Flask Shim] Downloading contents: {hash}")
        docs = doc_loader.get_url_documents(url)

        logger.info(f"[Flask Shim] Caching contents: {hash}")
        store.save_document_content(hash, docs)

    # register all tasks to run in group
    group(
        [
            analyzer_tasks.summarize_content.si(hash), # type: ignore
        ]
    ).apply_async()

    logger.info(f"[Flask Shim] Tasks requested for {url}")
    logger.info(f"[Flask Shim] Processing completed for {url}")
