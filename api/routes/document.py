import dataclasses
from flask import request, Flask

from services.persist import document


@dataclasses.dataclass
class ModifyAnnotationRequest:
    annotation: str


def register_routes(app: Flask):
    @app.post("/documents/<hash>/annotations")
    async def add_document_annotation(hash: str):
        request_body = ModifyAnnotationRequest(**request.json)  # type: ignore
        document.add_document_annotation(hash, request_body.annotation)

        return {}

    @app.get("/documents/<hash>/annotations")
    async def get_document_annotation(hash: str):
        document_annotations = document.get_document_annotations(hash)

        return {
            "annotations": document_annotations,
        }

    @app.delete("/documents/<hash>/annotations")
    async def remove_document_annotation(hash: str):
        request_body = ModifyAnnotationRequest(**request.json)  # type: ignore
        document.remove_document_annotation(hash, request_body.annotation)

        return {}
