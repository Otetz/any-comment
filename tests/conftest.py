import pytest

import any_comment
from app.common import db_conn


@pytest.fixture(scope='session')
def conn():
    with any_comment.app.app_context():
        return db_conn()
