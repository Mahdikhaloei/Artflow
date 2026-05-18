import pytest
from core import create_app
from core.config import TestingConfig
from core.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def db(app):
    _db.drop_all()
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(db):
    return db.session
