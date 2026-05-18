import pathlib

from core import models  # noqa: F401
from core import api
from core.config import Config
from core.extensions import apispec, celery, db, migrate
from core.tasks import poster_tasks  # noqa: F401
from flask import Flask, send_from_directory


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    configure_extensions(app)
    configure_apispec(app)
    register_blueprints(app)
    init_celery(app)

    BASE_DIR = pathlib.Path(__file__).parent.resolve()
    MEDIA_FOLDER = BASE_DIR / "media"

    @app.route("/media/<path:filename>")
    def media(filename):
        return send_from_directory(str(MEDIA_FOLDER), filename)

    return app


def configure_extensions(app):
    """Configure flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)


def configure_apispec(app):
    """Configure APISpec for swagger support"""
    apispec.init_app(app)
    apispec.spec.components.schema(
        "PaginatedResult",
        {
            "properties": {
                "total": {"type": "integer"},
                "pages": {"type": "integer"},
                "next": {"type": "string"},
                "prev": {"type": "string"},
            }
        },
    )


def register_blueprints(app):
    """Register all blueprints for application"""
    app.register_blueprint(api.views.blueprint)


def init_celery(app=None):
    app = app or create_app()
    celery.conf.update(app.config.get("CELERY", {}))

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
