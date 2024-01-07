import dataclasses
from flask import request, Flask
import flask_celery

from services.persist import task


@dataclasses.dataclass
class TaskActionBody:
    action: str


def register_routes(app: Flask):
    @app.get("/tasks")
    def list_registration_states():
        filters = list(
            map(lambda x: x.upper().strip(), request.args.getlist("filter", type=str))
        )
        registrations = task.get_processing_registrations()
        if filters:
            for filtered_status in filters:
                registrations = list(
                    filter(lambda x: x.status not in filtered_status, registrations)
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
            process_request = flask_celery.process_content.delay(
                task_request.hash, task_request.task_name
            )  # type: ignore

            return {
                "result_id": process_request.id,
                "hash": task_request.hash,
            }

        raise NotImplementedError()
