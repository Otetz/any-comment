import random

from elizabeth import Generic
from flaky import flaky
from flask import url_for

from app.common import db_conn, to_json
from app.types import User
from app.users import get_users, get_user, new_user

g = Generic('ru')


def test_get_list(client):
    res = client.get(url_for('users.users_list'))
    assert res is not None
    assert res.status_code == 200
    assert res.json is not None
    assert 'total' in res.json
    assert 'response' in res.json
    assert res.json['response'] is not None
    assert isinstance(res.json['response'], list)
    assert res.json['response'][0] is not None
    assert isinstance(res.json['response'][0], dict)
    assert len(res.json['response'][0]) == 3


def test_get_one(app, client):
    with app.app_context():
        user = random.choice(get_users(db_conn())[1])
        res = client.get(url_for('users.user', user_id=user['userid']))
        assert res.status_code == 200
        assert res is not None
        assert res.json is not None
        assert 'response' in res.json
        assert res.json['response'] is not None
        assert isinstance(res.json['response'], dict)
        assert len(res.json['response']) == 3
        for name in ['entityid', 'userid'] + User.data_fields:
            assert name in res.json['response']


def test_put(app, client):
    with app.app_context():
        user = random.choice(get_users(db_conn())[1])
        user_id = user['userid']
        name2 = name1 = user['name']
        while name2 == name1:
            name2 = g.personal.full_name(gender=random.choice(['male', 'female']))
        res = client.put(url_for('users.put_user', user_id=user_id), data=to_json({'name': name2}),
                         content_type='application/json')
        assert res.status_code == 200
        comment2 = get_user(db_conn(), user_id)
        for name in ['entityid', 'userid']:
            assert comment2[name] == user[name]
        assert comment2['name'] == name2


def test_post(app, client):
    with app.app_context():
        name = g.personal.full_name(gender=random.choice(['male', 'female']))
        res = client.post(url_for('users.post_user'), content_type='application/json', data=to_json({'name': name}))
        assert res.status_code == 200
        assert res is not None
        assert res.json is not None
        assert isinstance(res.json, dict)
        assert len(res.json) == 3
        for name in ['entityid', 'userid'] + User.data_fields:
            assert name in res.json
        user2 = get_user(db_conn(), res.json['userid'])
        assert user2 == res.json


def test_delete(app, client):
    with app.app_context():
        name = g.personal.full_name(gender=random.choice(['male', 'female']))
        user1 = new_user(db_conn(), {'name': name})
        res = client.delete(url_for('users.delete_user', user_id=user1['userid']))
        assert res.status_code == 200
        user3 = get_user(db_conn(), user1['userid'])
        assert user3 is None


@flaky
def test_first_level_comments(app, client):
    with app.app_context():
        users = get_users(db_conn())[1]
        user = random.choice(users)
        res = client.get(url_for('users.get_first_level_comments', user_id=user['userid']))
        assert res is not None
        assert res.status_code == 200
        assert res.json is not None
        assert 'total' in res.json
        assert 'response' in res.json
        assert res.json['response'] is not None
        assert isinstance(res.json['response'], list)
