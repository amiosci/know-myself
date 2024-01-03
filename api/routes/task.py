from flask import request, Flask

from services.persist import task


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
                "task_name": registration.task_name,
                "status": registration.status,
            }
            for registration in registrations
        ]
