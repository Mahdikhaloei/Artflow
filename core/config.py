import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".envs/.local/.artflow"
load_dotenv(dotenv_path=env_path)


POSTGRES_USER = os.getenv("DB_USER")
POSTGRES_PASSWORD = os.getenv("DB_PASS")
POSTGRES_PORT = os.getenv("DB_PORT")
POSTGRES_HOST = os.getenv("DB_HOST")
POSTGRES_DB = os.getenv("DB_NAME")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    UPLOADED_PHOTOS_DEST = "media/uploads"

    # ---------- SQLALCHEMY ----------
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---------- EMAIL ----------
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    CELERY = {
        "broker_url": os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"),
        "result_backend": os.getenv("CELERY_RESULT_BACKEND_URL", "redis://redis:6379/0"),
        "task_default_queue": "celery",
    }


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
