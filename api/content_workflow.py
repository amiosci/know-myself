import abc
import dataclasses
import enum
from langchain.docstore.document import Document
from typing import TypeVar, Generic
from doc_store import disk_store
from doc_store import doc_loader
from analyzers import extraction
from analyzers import summarize
from services import persist

ContentType = str

T = TypeVar("T")


@dataclasses.dataclass
class Context:
    # the primary hash being worked against
    hash: str
    url: str


class ContentTypeContainer(abc.ABC, Generic[T]):
    contentType: str

    async def get_output_type(self, context: Context) -> T:
        if not self.has_processed(context):
            content = await self._process_context(context)
            self._persist_output_type(context, content)
        else:
            content = await self._retrieve_output_type(context)

        return content

    @abc.abstractmethod
    def _persist_output_type(self, context: Context, results: T) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def _process_context(self, context: Context) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    async def _retrieve_output_type(self, context: Context) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def has_processed(self, context: Context) -> bool:
        raise NotImplementedError()


class DocumentContentContainer(ContentTypeContainer[list[Document]]):
    contentType = "content"

    def __init__(self):
        self._store = disk_store.default_store()

    def has_processed(self, context: Context) -> bool:
        return self._store.has_document_content(context.hash)

    async def _process_context(self, context: Context) -> list[Document]:
        return doc_loader.get_url_documents(context.url)

    def _persist_output_type(self, context: Context, results: list[Document]) -> None:
        self._store.save_document_content(context.hash, results)

    def _retrieve_output_type(self, context: Context) -> list[Document]:
        return self._store.restore_document_content(context.hash)


class DocumentEntitiesContainer(
    ContentTypeContainer[list[extraction.EntityRelationSchema]]
):
    contentType = "extracted-relations"

    def __init__(self):
        self._store = disk_store.default_store()

    def has_processed(self, context: Context) -> bool:
        return self._store.has_entity_relations(context.hash)

    async def _process_context(
        self, context: Context
    ) -> list[extraction.EntityRelationSchema] | None:
        content_provider = DocumentContentContainer()
        content = await content_provider.get_output_type(context)
        return await extraction.extract_entity_relations(content)

    def _persist_output_type(
        self, context: Context, results: list[extraction.EntityRelationSchema]
    ) -> None:
        self._store.save_entity_relations(context.hash, results)

    def _retrieve_output_type(
        self, context: Context
    ) -> list[extraction.EntityRelationSchema]:
        return self._store.load_entity_relations(context.hash)


class TaskResultType(enum.Enum):
    SKIPPED = 0
    PROCESSED = 1
    FAILED = 2


@dataclasses.dataclass
class TaskResult:
    result_type: TaskResultType


class ProcessorBase(abc.ABC):
    @abc.abstractmethod
    async def process_context(self, context: Context) -> TaskResult:
        raise NotImplementedError()


class SummarizeContent(ProcessorBase):
    async def process_context(self, context: Context) -> TaskResult:
        if persist.has_summary(context.hash):
            return TaskResult(result_type=TaskResultType.SKIPPED)

        content_provider = DocumentContentContainer()
        content = await content_provider.get_output_type(context)
        summary = await summarize.summarize_document(content)
        persist.save_summary(context.hash, summary)
        return TaskResult(result_type=TaskResultType.PROCESSED)


# To be replaced by consumption of `extracted-relations`
class ExtractContentRelations(ProcessorBase):
    async def process_context(self, context: Context) -> TaskResult:
        content_provider = DocumentEntitiesContainer()
        if content_provider.has_processed(context):
            return TaskResult(result_type=TaskResultType.SKIPPED)

        await content_provider.get_output_type(context)
        return TaskResult(result_type=TaskResultType.PROCESSED)


class BaseWorkflow(abc.ABC):
    pass


class AddToKGWorkflow(BaseWorkflow):
    pass
