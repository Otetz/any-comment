import pytest

from any_comment import create_app
from app.common import db_conn, redis_conn


@pytest.fixture(scope='session')
def app():
    service = create_app()
    return service


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def conn(app):
    with app.app_context():
        return db_conn()


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def r_conn(app):
    with app.app_context():
        return redis_conn()
