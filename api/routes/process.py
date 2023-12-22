import dataclasses
from flask import request, Flask
import url_tools
import flask_celery

from services import persist


@dataclasses.dataclass
class GetProcessingResultsContentRequest:
    summary: bool = True


@dataclasses.dataclass
class GenerateSummaryRequest:
    url: str
    title: str

    force_process: bool = False


def register_routes(app: Flask):
    @app.get("/tasks")
    def list_registration_states():
        filters = list(
            map(lambda x: x.upper().strip(), request.args.getlist("filter", type=str))
        )
        registrations = persist.get_processing_registrations()
        if filters:
            for filtered_status in filters:
                registrations = list(
                    filter(lambda x: x.status not in filtered_status, registrations)
                )

        return [
            {
                "url": registration.url,
                "hash": registration.hash,
                "status": registration.status,
            }
            for registration in registrations
            if registration.status != "None"
        ]

    @app.get("/process")
    def list_registration_results():
        return [
            {
                "url": registration.url,
                "hash": registration.hash,
                "has_summary": registration.has_summary,
            }
            for registration in persist.get_processing_registrations()
        ]

    @app.post("/process")
    def register_url():
        request_body = GenerateSummaryRequest(**request.json) # type: ignore
        target_url = url_tools.extract_target_url(request_body.url)
        target_url_hash = url_tools.hash_url(target_url)
        registration = persist.get_processing_registration(target_url_hash)
        if registration is not None and not request_body.force_process:
            print("URL already processed")
            return {"result_id": None, "hash": target_url_hash}

        # use target URL to dedupe against requests with fragment/query changes
        process_request = flask_celery.process_content.delay(
            target_url_hash, target_url
        )  # type: ignore
        persist.update_processing_action(
            target_url_hash,
            target_url,
            process_request.id,
            "PENDING",
        )

        return {"result_id": process_request.id, "hash": target_url_hash}

    @app.post("/process/<hash>/results")
    def get_processing_result_content(hash: str):
        value = {}
        process_result = None
        task_id = None

        registration = persist.get_processing_registration(hash)
        if registration is not None:
            task_id = registration.task_id
            process_result = persist.get_task_result(task_id)
            if process_result == "SUCCESS":
                request_body = GetProcessingResultsContentRequest(**request.json) # type: ignore
                if request_body.summary:
                    value["summary"] = persist.get_summary(hash)
        return {
            "resultId": task_id,
            "status": process_result,
            "hash": hash,
            "values": value,
        }
