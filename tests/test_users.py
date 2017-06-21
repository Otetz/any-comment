import pytest

import any_comment
from app.common import db_conn
from app.users import get_users


@pytest.fixture
def conn():
    with any_comment.app.app_context():
        return db_conn()


# noinspection PyShadowingNames
def test_get_users(conn):
    users = get_users(conn)
    assert users is not None
    assert isinstance(users, list)
    assert len(users) > 0
    assert users[0] is not None
    assert isinstance(users[0], dict)
    assert len(users[0]) == 3
    assert 'entityid' in users[0]
    assert isinstance(users[0]['entityid'], int)
    assert users[0]['entityid'] != 0
    assert 'userid' in users[0]
    assert isinstance(users[0]['userid'], int)
    assert users[0]['userid'] != 0
    assert 'name' in users[0]
    assert isinstance(users[0]['name'], str)
    assert users[0]['name'] != ''
