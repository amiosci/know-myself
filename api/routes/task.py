import dataclasses
from flask import request, Flask
import flask_celery
from itertools import chain

from services.persist import task


@dataclasses.dataclass
class TaskActionBody:
    action: str


def register_routes(app: Flask):
    def _get_task_type_statuses(task_type: str) -> list[str]:
        if task_type == "all":
            return []
        elif task_type == "pending":
            return ["PENDING", "STARTED"]
        elif task_type == "complete":
            return ["COMPLETED"]
        elif task_type == "failed":
            return ["TIMEOUT", "FAILED"]

        raise ValueError(f"Unsupported task_type {task_type}")

    @app.get("/tasks")
    def list_registration_states():
        task_types = request.args.getlist(
            "type",
            type=str,
        )

        if not task_types:
            task_types = ["complete"]

        supported_task_types = ["pending", "complete", "failed", "all"]
        if any(map(lambda x: x not in supported_task_types, task_types)):
            raise ValueError("Invalid type argument")

        status_filters = list(
            chain.from_iterable(map(_get_task_type_statuses, task_types))
        )

        registrations = task.get_processing_registrations()
        if len(status_filters) > 0:
            registrations = filter(lambda x: x.status in status_filters, registrations)

        show_retried_tasks = request.args.get("include_retried", False, type=bool)
        registrations = filter(
            lambda x: x.retry_task_id is None or show_retried_tasks, registrations
        )

        return [
            {
                "url": registration.url,
                "hash": registration.hash,
                "task_id": registration.task_id,
                "task_name": registration.task_name,
                "status": registration.status,
            }
            for registration in registrations
        ]

    @app.post("/tasks/<task_id>/action")
    def reprocess_task(task_id: str):
        request_body = TaskActionBody(**request.json)  # type: ignore
        # re-request task type
        if request_body.action == "reprocess":
            task_request = task.get_task_request(task_id)
            if task_request is None:
                raise ValueError("No such task exists")
            reprocess_task = flask_celery.process_content.delay(
                task_request.hash, task_request.task_name
            )  # type: ignore

            task.set_retry_child(task_id, reprocess_task.id)

            return {
                "result_id": reprocess_task.id,
                "hash": task_request.hash,
            }

        raise NotImplementedError()
