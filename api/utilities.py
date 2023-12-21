from flask import Flask
from celery import Celery, Task
from flask_cors import CORS


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost:6379/0",
            # relevant results are captured in long-term storage
            result_backend="redis://localhost:6379/0",
            task_ignore_result=True,
        ),
    )
    app.config.from_prefixed_env() # type: ignore
    celery_init_app(app)
    return app
