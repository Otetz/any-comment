import os

import pytest

from any_comment import app, db_conn
from app.users import get_users

app.config.from_object(os.environ['APP_SETTINGS'])


@pytest.fixture
def conn():
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
