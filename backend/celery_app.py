import os
from celery import Celery, Task
from backend.main import create_app   # ✅ correct factory location

def make_celery() -> Celery:
    # 1) Build the Flask app
    flask_app = create_app()

    # 2) Init Celery with env‑driven broker/backend (defaults = local Redis)
    celery = Celery(
        flask_app.import_name,
        broker=os.getenv("CELERY_BROKER", "redis://localhost:6379/0"),
        backend=os.getenv("CELERY_BACKEND", "redis://localhost:6379/1"),
        include=["backend.tasks.geocode_tasks"],
    )

    # 3) Copy Flask config into Celery for good measure
    celery.conf.update(flask_app.config)

    # 4) Ensure every task runs inside the Flask app context
    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery_app = make_celery()
