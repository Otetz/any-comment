import random

import pytest

import any_comment
from app.common import db_conn
from app.posts import get_posts, get_post, new_post, remove_post, update_post
from elizabeth import Generic

from app.users import get_users

g = Generic('ru')


@pytest.fixture
def conn():
    with any_comment.app.app_context():
        return db_conn()


# noinspection PyShadowingNames
def test_get_posts(conn):
    posts = get_posts(conn)
    assert posts is not None
    assert isinstance(posts, list)
    assert len(posts) > 0
    assert posts[0] is not None
    assert isinstance(posts[0], dict)
    assert len(posts[0]) == 5
    for field in ['entityid', 'postid', 'userid']:
        assert field in posts[0]
        assert isinstance(posts[0][field], int)
        assert posts[0][field] != 0
    for field in ['title', 'text']:
        assert field in posts[0]
        assert isinstance(posts[0][field], str)
        assert posts[0][field] != ''


# noinspection PyShadowingNames
def test_get_post(conn):
    post = get_post(conn, get_posts(conn)[0]['postid'])
    assert post is not None
    assert isinstance(post, dict)
    assert len(post) == 5
    assert 'title' in post
    assert isinstance(post['title'], str)
    assert post['title'] != ''


# noinspection PyShadowingNames
def test_get_post_error(conn):
    post = get_post(conn, 0)
    assert post is None


# noinspection PyShadowingNames
def test_new_post(conn):
    userid = random.choice(get_users(conn))['userid']
    title = g.text.text(quantity=1)
    text = g.text.text(quantity=random.randrange(5, 11))
    post = new_post(conn, {'userid': userid, 'title': title, 'text': text})
    assert post is not None
    assert isinstance(post, dict)
    assert len(post) == 5
    assert 'postid' in post
    assert isinstance(post['postid'], int)
    assert post['postid'] != 0
    post2 = get_post(conn, post['postid'])
    assert post2 is not None
    assert post2['title'] == title
    remove_post(conn, post['postid'])


# noinspection PyShadowingNames
def test_remove_post(conn):
    userid = random.choice(get_users(conn))['userid']
    title = g.text.text(quantity=1)
    text = g.text.text(quantity=random.randrange(5, 11))
    post1 = new_post(conn, {'userid': userid, 'title': title, 'text': text})
    post2 = get_post(conn, post1['postid'])
    cnt = remove_post(conn, post2['postid'])
    assert cnt == 1
    post3 = get_post(conn, post1['postid'])
    assert post3 is None


# noinspection PyShadowingNames
def test_remove_wrong_post(conn):
    cnt = remove_post(conn, 0)
    assert cnt == 0


# noinspection PyShadowingNames
def test_update_post(conn):
    userid = random.choice(get_users(conn))['userid']
    title2 = title1 = g.text.text(quantity=1)
    text = g.text.text(quantity=random.randrange(5, 11))
    post1 = new_post(conn, {'userid': userid, 'title': title1, 'text': text})
    assert post1 is not None
    post2 = get_post(conn, post1['postid'])
    assert post2 is not None
    assert post2['title'] == title1
    while title2 == title1:
        title2 = g.text.text(quantity=1)
    res = update_post(conn, post1['postid'], {'userid': userid, 'title': title2, 'text': text})
    assert res is not None
    assert res == 1
    post3 = get_post(conn, post1['postid'])
    assert post3 is not None
    assert post3['postid'] == post1['postid']
    assert post3['entityid'] == post1['entityid']
    assert post3['userid'] == post1['userid']
    assert post3['title'] != post1['title']
    assert post3['title'] == title2
    assert post3['text'] == post1['text']
    remove_post(conn, post1['postid'])
