import dataclasses
from flask import request, Flask

from services.persist import document


@dataclasses.dataclass
class AddAnnotationRequest:
    annotation: str


def register_routes(app: Flask):
    @app.post("/documents/<hash>/annotations")
    async def add_document_annotation(hash: str):
        request_body = AddAnnotationRequest(**request.json)  # type: ignore
        document.add_document_annotation(hash, request_body.annotation)

        return {}
