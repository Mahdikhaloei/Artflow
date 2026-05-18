from core import create_app, init_celery

flask_app = create_app()
celery_app = init_celery(flask_app)
celery_app.conf.imports = celery_app.conf.imports + ("core.tasks.poster_tasks",)

app = celery_app
