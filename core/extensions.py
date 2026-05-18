"""Extensions registry

All extensions here are used as singletons and
initialized in application factory
"""
from celery import Celery
from core.commons.apispec import APISpecExt
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
apispec = APISpecExt()
celery = Celery()
