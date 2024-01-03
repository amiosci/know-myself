import dataclasses
from flask import jsonify, Flask

from content_workflow import DocumentSummaryContainer, Context


@dataclasses.dataclass
class ContentSummaryResponse:
    hash: str
    summary: str | None

    # @property requires custom logic to support jsonify, don't care for now
    hasSummary: bool

    @classmethod
    def for_hash_response(
        cls, hash: str, summary: str | None, **kwargs
    ) -> "ContentSummaryResponse":
        has_summary = kwargs.pop("has_summary", summary is not None)
        return cls(hash, summary, has_summary, **kwargs)


def register_routes(app: Flask):
    @app.get("/summary/<hash>")
    async def has_summary(hash: str):
        content_retriever = DocumentSummaryContainer()
        context = Context(hash=hash)
        if content_retriever.has_processed(context):
            summary = await content_retriever.get_output_type(context)
        else:
            summary = None
        response = ContentSummaryResponse.for_hash_response(hash, summary)
        return jsonify(response)
