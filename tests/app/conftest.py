import pytest

from any_comment import create_app
from app.common import db_conn


@pytest.fixture(scope='session')
def conn():
    app = create_app()
    with app.app_context():
        return db_conn()
