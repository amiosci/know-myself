import abc
import dataclasses
import enum
import io
import traceback

from langchain.docstore.document import Document
from typing import TypeVar, Generic
from doc_store import disk_store
from doc_store import doc_loader
from analyzers import extraction
from analyzers import summarize
from services.persist import summary, document

ContentType = str

T = TypeVar("T")


@dataclasses.dataclass
class Context:
    # the primary hash being worked against
    hash: str

    # Force the processor to re-run, independent of prior results.
    # Generally speaking, this will overwrite the previous results.
    force_process: bool = False

    def __str__(self) -> str:
        return f"Force: [{self.force_process}] Hash: [{self.hash}]"


class ContentTypeContainer(abc.ABC, Generic[T]):
    contentType: str

    async def get_output_type(self, context: Context) -> T:
        if not self.has_processed(context):
            content = await self._process_context(context)
            self._store_content(context, content)
        else:
            content = await self._load_content(context)

        return content

    @abc.abstractmethod
    def has_processed(self, context: Context) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def _store_content(self, context: Context, results: T) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def _process_context(self, context: Context) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    async def _load_content(self, context: Context) -> T:
        raise NotImplementedError()


class DocumentContentContainer(ContentTypeContainer[list[Document]]):
    contentType = "content"

    def __init__(self, **kwargs):
        self._store = disk_store.default_store(**kwargs)

    def has_processed(self, context: Context) -> bool:
        return self._store.has_document_content(context.hash)

    async def _process_context(self, context: Context) -> list[Document]:
        url = document.get_hash_url(context.hash)
        return doc_loader.get_url_documents(url)

    def _store_content(self, context: Context, results: list[Document]) -> None:
        self._store.save_document_content(context.hash, results)

    async def _load_content(self, context: Context) -> list[Document]:
        return self._store.restore_document_content(context.hash)


class DocumentEntitiesContainer(
    ContentTypeContainer[list[extraction.EntityRelationSchema]]
):
    contentType = "extracted-relations"

    def __init__(self, **kwargs):
        self._store = disk_store.default_store(**kwargs)

    def has_processed(self, context: Context) -> bool:
        return self._store.has_entity_relations(context.hash)

    async def _process_context(
        self, context: Context
    ) -> list[extraction.EntityRelationSchema] | None:
        content_provider = DocumentContentContainer()
        content = await content_provider.get_output_type(context)
        return await extraction.extract_entity_relations(content)

    def _store_content(
        self, context: Context, results: list[extraction.EntityRelationSchema]
    ) -> None:
        self._store.save_entity_relations(context.hash, results)

    async def _load_content(
        self, context: Context
    ) -> list[extraction.EntityRelationSchema]:
        return self._store.load_entity_relations(context.hash)


class DocumentSummaryContainer(ContentTypeContainer[str]):
    contentType = "document-summary"

    def __init__(self):
        self._store = disk_store.default_store()

    def has_processed(self, context: Context) -> bool:
        return summary.has_summary(context.hash)

    async def _process_context(self, context: Context) -> str | None:
        content_provider = DocumentContentContainer()
        content = await content_provider.get_output_type(context)
        return await summarize.summarize_document(content)

    def _store_content(self, context: Context, results: str) -> None:
        summary.save_summary(context.hash, results)

    async def _load_content(self, context: Context) -> str:
        document_summary = summary.get_summary(context.hash)
        if document_summary is not None:
            return document_summary

        raise RuntimeError("Summary must exist before loading")


class TaskResultType(enum.Enum):
    SKIPPED = 0
    PROCESSED = 1
    FAILED = 2


@dataclasses.dataclass
class TaskResult:
    result_type: TaskResultType
    message: str | None = None

    def __str__(self) -> str:
        x = f"{self.result_type}"
        if self.message is not None:
            x += f": {self.message}"
        return x


class DocumentProcessorError(Exception):
    """Used to propagate a handled failure during document processing."""


class ProcessorBase(abc.ABC):
    async def process_context(self, context: Context) -> TaskResult:
        if not context.force_process:
            if await self._skip_processor(context):
                return TaskResult(result_type=TaskResultType.SKIPPED)
        try:
            await self._run_processor(context)
            return TaskResult(result_type=TaskResultType.PROCESSED)
        except DocumentProcessorError as e:
            return TaskResult(
                result_type=TaskResultType.FAILED,
                message=str(e.args[0]),
            )
        except Exception as e:
            exception_writer = io.StringIO()
            traceback.print_exc(file=exception_writer)
            exception_message = exception_writer.read()
            message = f"Unexpected exception: {exception_message}"
            return TaskResult(
                result_type=TaskResultType.FAILED,
                message=message,
            )

    @abc.abstractmethod
    async def _run_processor(self, context: Context) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def _skip_processor(self, context: Context) -> bool:
        raise NotImplementedError()


class SummarizeContent(ProcessorBase):
    async def _skip_processor(self, context: Context) -> bool:
        return summary.has_summary(context.hash)

    async def _run_processor(self, context: Context) -> None:
        content_provider = DocumentContentContainer()
        content = await content_provider.get_output_type(context)
        document_summary = await summarize.summarize_document(content)
        if len(document_summary) == 0:
            raise DocumentProcessorError("No summary created for document")
        summary.save_summary(context.hash, document_summary)


# To be replaced by consumption of `extracted-relations`
class ExtractContentRelations(ProcessorBase):
    _content_provider: DocumentEntitiesContainer

    def __init__(self):
        self._content_provider = DocumentEntitiesContainer()

    async def _skip_processor(self, context: Context) -> bool:
        return self._content_provider.has_processed(context)

    async def _run_processor(self, context: Context) -> None:
        extracted_entities = await self._content_provider.get_output_type(context)
        if len(extracted_entities) == 0:
            raise DocumentProcessorError("No entities extracted for document")
