import dataclasses
from flask import request, Flask
import flask_celery

from services.persist import task, document, summary
from routes import url_tools

from loaders.loaders import get_loader_spec


@dataclasses.dataclass
class GetProcessingResultsContentRequest:
    summary: bool = True


@dataclasses.dataclass
class GenerateSummaryRequest:
    url: str
    title: str

    force_process: bool = True


def register_routes(app: Flask):
    @app.get("/process")
    def list_registration_results():
        return [
            {
                "url": registration.url,
                "hash": registration.hash,
                "has_summary": registration.has_summary,
            }
            for registration in document.get_loaded_documents()
        ]

    @app.post("/process")
    def register_url():
        request_body = GenerateSummaryRequest(**request.json)  # type: ignore

        target_url = url_tools.extract_target_url(request_body.url)
        target_url_hash = url_tools.hash_url(target_url)
        loader_spec = get_loader_spec(target_url)
        if loader_spec is None:
            raise ValueError("Could not process URL")

        has_processed_spec = document.has_loader_spec_registered(loader_spec)
        if has_processed_spec and not request_body.force_process:
            print("URL already processed")
            return {"result_id": None, "hash": target_url_hash}

        document.register_document(
            target_url_hash,
            target_url,
            loader_spec,
            handle_exists=request_body.force_process,
        )

        # use target URL to dedupe against requests with fragment/query changes
        process_request = flask_celery.process_content.delay(
            target_url_hash
        )  # type: ignore

        return {
            "result_id": process_request.id,
            "hash": target_url_hash,
        }

    @app.post("/process/<hash>/results")
    def get_processing_result_content(hash: str):
        value = {}
        process_result = None
        task_id = None

        registration = task.get_processing_registration(hash)
        if registration is not None:
            task_id = registration.task_id
            process_result = task.get_task_result(task_id)
            if process_result == "SUCCESS":
                request_body = GetProcessingResultsContentRequest(**request.json)  # type: ignore
                if request_body.summary:
                    value["summary"] = summary.get_summary(hash)
        return {
            "resultId": task_id,
            "status": process_result,
            "hash": hash,
            "values": value,
        }
