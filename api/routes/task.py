import dataclasses
from flask import request, Flask
import flask_celery
from itertools import chain

from services.persist import task


@dataclasses.dataclass
class TaskActionBody:
    action: str


def _get_task_type_statuses(task_type: str) -> list[str]:
    match task_type:
        case "all":
            return []
        case "pending":
            return ["PENDING", "STARTED"]
        case "complete":
            return ["COMPLETED"]
        case "failed":
            return ["TIMEOUT", "FAILED"]

    raise ValueError(f"Unsupported task_type {task_type}")


def register_routes(app: Flask):
    @app.get("/tasks")
    def list_registration_states():
        task_types = request.args.getlist(
            "type",
            type=str,
        )

        if not task_types:
            task_types = ["complete"]

        supported_task_types = [
            "pending",
            "complete",
            "failed",
            "all",
        ]
        if any(map(lambda x: x not in supported_task_types, task_types)):
            raise ValueError("Invalid type argument")

        status_filters = list(
            chain.from_iterable(map(_get_task_type_statuses, task_types))
        )

        registrations = task.get_processing_registrations()
        if status_filters:
            registrations = filter(lambda x: x.status in status_filters, registrations)

        show_retried_tasks = request.args.get("include_retried", False, type=bool)
        registrations = filter(
            lambda x: x.retry_task_id is None or show_retried_tasks, registrations
        )

        return [dataclasses.asdict(registration) for registration in registrations]

    @app.post("/tasks/<task_id>/action")
    def reprocess_task(task_id: str):
        request_body = TaskActionBody(**request.json)  # type: ignore
        match request_body.action:
            case "reprocess":
                # re-request task type
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
