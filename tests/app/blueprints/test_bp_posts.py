import random

from elizabeth import Generic
from flaky import flaky
from flask import url_for

from app.common import db_conn, to_json
from app.posts import get_posts, get_post, new_post
from app.types import Post
from app.users import get_users

g = Generic('ru')


def test_get_list(client):
    res = client.get(url_for('posts.posts_list'))
    assert res is not None
    assert res.status_code == 200
    assert res.json is not None
    assert 'total' in res.json
    assert 'response' in res.json
    assert res.json['response'] is not None
    assert isinstance(res.json['response'], list)
    assert res.json['response'][0] is not None
    assert isinstance(res.json['response'][0], dict)
    assert len(res.json['response'][0]) == 5


def test_get_one(app, client):
    with app.app_context():
        post = random.choice(get_posts(db_conn())[1])
        res = client.get(url_for('posts.post', post_id=post['postid']))
        assert res.status_code == 200
        assert res is not None
        assert res.json is not None
        assert 'response' in res.json
        assert res.json['response'] is not None
        assert isinstance(res.json['response'], dict)
        assert len(res.json['response']) == 5
        for name in ['entityid', 'postid'] + Post.data_fields:
            assert name in res.json['response']


def test_put(app, client):
    with app.app_context():
        post = random.choice(get_posts(db_conn())[1])
        post_id = post['postid']
        text2 = text1 = post['text']
        while text2 == text1:
            text2 = g.text.text(quantity=random.randrange(5, 11))
        res = client.put(url_for('posts.put_post', post_id=post_id), data=to_json({'text': text2}),
                         content_type='application/json')
        assert res.status_code == 200
        post2 = get_post(db_conn(), post_id)
        for name in ['entityid', 'postid']:
            assert post2[name] == post[name]
        assert post2['text'] == text2


def test_post(app, client):
    with app.app_context():
        userid = random.choice(get_users(db_conn())[1])['userid']
        title = g.text.text(quantity=1)
        text = g.text.text(quantity=random.randrange(5, 11))
        res = client.post(url_for('posts.post_post'), content_type='application/json',
                          data=to_json({'userid': userid, 'title': title, 'text': text}))
        assert res.status_code == 200
        assert res is not None
        assert res.json is not None
        assert isinstance(res.json, dict)
        assert len(res.json) == 5
        for name in ['entityid', 'postid'] + Post.data_fields:
            assert name in res.json
        post2 = get_post(db_conn(), res.json['postid'])
        assert post2 == res.json


def test_delete(app, client):
    with app.app_context():
        userid = random.choice(get_users(db_conn())[1])['userid']
        title = g.text.text(quantity=1)
        text = g.text.text(quantity=random.randrange(5, 11))
        post1 = new_post(db_conn(), {'userid': userid, 'title': title, 'text': text})
        res = client.delete(url_for('posts.delete_post', post_id=post1['postid']))
        assert res.status_code == 200
        post3 = get_post(db_conn(), post1['postid'])
        assert post3 is None


@flaky
def test_first_level_comments(app, client):
    with app.app_context():
        posts = get_posts(db_conn())[1]
        post = random.choice(posts)
        res = client.get(url_for('posts.get_first_level_comments', post_id=post['postid']))
        assert res is not None
        assert res.status_code == 200
        assert res.json is not None
        assert 'total' in res.json
        assert 'response' in res.json
        assert res.json['response'] is not None
        assert isinstance(res.json['response'], list)


@flaky(max_runs=10, min_passes=1)
def test_get_descendants(app, client):
    with app.app_context():
        post = random.choice(get_posts(db_conn())[1])
        res = client.get(url_for('posts.get_descendants', post_id=post['postid']))
        assert res is not None
        assert res.status_code == 200
        assert res.json is not None
        assert len(res.json) >= 1
