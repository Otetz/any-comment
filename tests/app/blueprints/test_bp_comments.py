import datetime
import random
from urllib.parse import urlparse

import dateutil.parser
from dateutil.tz import tzlocal
from elizabeth import Generic
from flaky import flaky
from flask import url_for

from app.comments import Comment, get_comments, get_comment, new_comment
from app.common import db_conn, to_json
from app.posts import get_posts, first_level_comments as post_first_level_comments
from app.users import get_users

g = Generic('ru')


def test_get_list(client):
    res = client.get(url_for('comments.comments_list'))
    assert res is not None
    assert res.status_code == 200
    assert res.json is not None
    assert 'total' in res.json
    assert 'response' in res.json
    assert res.json['response'] is not None
    assert isinstance(res.json['response'], list)
    assert res.json['response'][0] is not None
    assert isinstance(res.json['response'][0], dict)
    assert len(res.json['response'][0]) == 7


def test_get_one(app, client):
    with app.app_context():
        comment = random.choice(get_comments(db_conn())[1])
        res = client.get(url_for('comments.comment', comment_id=comment['commentid']))
        assert res.status_code == 200
        assert res is not None
        assert res.json is not None
        assert 'response' in res.json
        assert res.json['response'] is not None
        assert isinstance(res.json['response'], dict)
        assert len(res.json['response']) == 7
        for name in ['entityid', 'commentid'] + Comment.data_fields:
            if name == 'userid':
                continue
            assert name in res.json['response']
        assert isinstance(res.json['response']['author'], dict)
        assert len(res.json['response']['author']) == 2
        assert 'userid' in res.json['response']['author']
        assert isinstance(res.json['response']['author']['userid'], int)
        assert res.json['response']['author']['userid'] > 0
        assert 'name' in res.json['response']['author']
        assert isinstance(res.json['response']['author']['name'], str)
        assert res.json['response']['author']['name'] != ''
        assert dateutil.parser.parse(res.json['response']['datetime'])


def test_put(app, client):
    with app.app_context():
        comment = random.choice(get_comments(db_conn())[1])
        comment_id = comment['commentid']
        text2 = text1 = comment['text']
        while text2 == text1:
            text2 = g.text.text(quantity=random.randrange(1, 3))
        res = client.put(url_for('comments.put_comment', comment_id=comment_id), data=to_json({'text': text2}),
                         content_type='application/json')
        assert res.status_code == 200
        comment2 = get_comment(db_conn(), comment_id)
        for name in ['entityid', 'commentid', 'author', 'parentid', 'datetime', 'deleted']:
            assert comment2[name] == comment[name]
        assert comment2['text'] == text2


def test_post(app, client):
    with app.app_context():
        userid = random.choice(get_users(db_conn())[1])['userid']
        parentid = random.choice(get_comments(db_conn())[1])['entityid']
        text = g.text.text(quantity=random.randrange(1, 3))
        dt = datetime.datetime.now(tz=tzlocal())
        res = client.post(url_for('comments.post_comment'), content_type='application/json',
                          data=to_json({'userid': userid, 'parentid': parentid, 'text': text}))
        assert res.status_code == 302
        assert urlparse(res.location).path.startswith(url_for('comments.comments_list'))
        new_comment_id = int(urlparse(res.location).path.split('/')[-1])
        comment2 = get_comment(db_conn(), new_comment_id)
        for name in ['entityid', 'commentid'] + Comment.data_fields:
            if name != 'userid':
                assert name in comment2
        assert comment2['author']['userid'] == userid
        assert comment2['parentid'] == parentid
        assert comment2['text'] == text
        assert (comment2['datetime'] - dt).microseconds < 10000


def test_delete(app, client):
    with app.app_context():
        userid = random.choice(get_users(db_conn())[1])['userid']
        parentid = random.choice(get_comments(db_conn())[1])['entityid']
        text = g.text.text(quantity=random.randrange(1, 3))
        comment1_id = new_comment(db_conn(), {'userid': userid, 'parentid': parentid, 'text': text})[0]
        assert comment1_id is not None
        res = client.delete(url_for('comments.delete_comment', comment_id=comment1_id))
        assert res.status_code == 200
        comment3 = get_comment(db_conn(), comment1_id)
        assert comment3 is not None
        assert comment3['deleted'] is True


@flaky
def test_first_level_comments(app, client):
    with app.app_context():
        posts = get_posts(db_conn())[1]
        comments = []
        while not comments:
            post = random.choice(posts)
            comments = post_first_level_comments(db_conn(), post['postid'])[1]
        res = client.get(url_for('comments.get_first_level_comments', comment_id=random.choice(comments)['commentid']))
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
        comment = random.choice(get_comments(db_conn())[1])
        res = client.get(url_for('comments.get_descendants', comment_id=comment['commentid']))
        assert res is not None
        assert res.status_code == 200
        assert res.json is not None
        assert len(res.json) >= 1
