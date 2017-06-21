import random

import pytest

import any_comment
from app.common import db_conn
from app.users import get_users, get_user, new_user, remove_user
from elizabeth import Generic

g = Generic('ru')


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


# noinspection PyShadowingNames
def test_get_user(conn):
    user = get_user(conn, get_users(conn)[0]['userid'])
    assert user is not None
    assert isinstance(user, dict)
    assert len(user) == 3
    assert 'entityid' in user
    assert isinstance(user['entityid'], int)
    assert user['entityid'] != 0
    assert 'userid' in user
    assert isinstance(user['userid'], int)
    assert user['userid'] != 0
    assert 'name' in user
    assert isinstance(user['name'], str)
    assert user['name'] != ''


# noinspection PyShadowingNames
def test_get_user_error(conn):
    user = get_user(conn, 0)
    assert user is None


# noinspection PyShadowingNames
def test_new_user(conn):
    name = g.personal.full_name(gender=random.choice(['male', 'female']))
    data = {'name': name}
    user = new_user(conn, data)
    assert user is not None
    assert isinstance(user, dict)
    assert len(user) == 3
    assert 'entityid' in user
    assert isinstance(user['entityid'], int)
    assert user['entityid'] != 0
    assert 'userid' in user
    assert isinstance(user['userid'], int)
    assert user['userid'] != 0
    assert 'name' in user
    assert isinstance(user['name'], str)
    assert user['name'] == name
    user2 = get_user(conn, user['userid'])
    assert user2 is not None
    assert user2['name'] == name
    remove_user(conn, user['userid'])


# noinspection PyShadowingNames
def test_remove_user(conn):
    name = g.personal.full_name(gender=random.choice(['male', 'female']))
    data = {'name': name}
    user1 = new_user(conn, data)
    user2 = get_user(conn, user1['userid'])
    cnt = remove_user(conn, user2['userid'])
    assert cnt == 1
    user3 = get_user(conn, user1['userid'])
    assert user3 is None


# noinspection PyShadowingNames
def test_remove_wrong_user(conn):
    cnt = remove_user(conn, 0)
    assert cnt == 0
