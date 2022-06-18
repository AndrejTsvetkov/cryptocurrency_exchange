# pylint: disable=redefined-outer-name
import os
import tempfile

import pytest

from config import TestConfig
from exchange import create_app
from exchange.models import Base


# created once for all tests
@pytest.fixture(scope='session')
def app():
    db_fd, database_file = tempfile.mkstemp()

    TestConfig.SQLALCHEMY_DATABASE_URI = f'sqlite:///{database_file}'
    app = create_app(TestConfig)

    yield app

    os.close(db_fd)
    os.unlink(database_file)


# created once for all tests
@pytest.fixture(scope='session')
def client(app):
    with app.test_client() as client:
        return client


@pytest.fixture(autouse=True)
def _init_db(app):
    with app.app_context():
        Base.metadata.create_all(app.db_engine)
        # fill_db(app)
        yield
        Base.metadata.drop_all(app.db_engine)
