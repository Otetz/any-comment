import datetime
import random

import pytest

import any_comment
from app.common import db_conn
from app.comments import get_comments, get_comment, new_comment, remove_comment, update_comment
from elizabeth import Generic

from app.users import get_users

g = Generic('ru')


@pytest.fixture
def conn():
    with any_comment.app.app_context():
        return db_conn()


# noinspection PyShadowingNames
def test_get_comments(conn):
    comments = get_comments(conn)[1]
    assert comments is not None
    assert isinstance(comments, list)
    assert len(comments) > 0
    assert comments[0] is not None
    assert isinstance(comments[0], dict)
    assert len(comments[0]) == 7
    for field in ['entityid', 'commentid', 'userid', 'parentid']:
        assert field in comments[0]
        assert isinstance(comments[0][field], int)
        assert comments[0][field] != 0
    for field in ['text']:
        assert field in comments[0]
        assert isinstance(comments[0][field], str)
        assert comments[0][field] != ''
    for field in ['deleted']:
        assert field in comments[0]
        assert isinstance(comments[0][field], bool)
        assert comments[0][field] is not None
    for field in ['datetime']:
        assert field in comments[0]
        assert isinstance(comments[0][field], datetime.datetime)
        assert comments[0][field] is not None


# noinspection PyShadowingNames
def test_get_comment(conn):
    comment = get_comment(conn, get_comments(conn)[1][0]['commentid'])
    assert comment is not None
    assert isinstance(comment, dict)
    assert len(comment) == 7
    assert 'text' in comment
    assert isinstance(comment['text'], str)
    assert comment['text'] != ''


# noinspection PyShadowingNames
def test_get_comment_error(conn):
    comment = get_comment(conn, 0)
    assert comment is None


# noinspection PyShadowingNames
def test_new_comment(conn):
    userid = random.choice(get_users(conn))['userid']
    parentid = random.choice(get_comments(conn)[1])['entityid']
    text = g.text.text(quantity=random.randrange(1, 3))
    dt = datetime.datetime.now()
    comment = new_comment(conn, {'userid': userid, 'parentid': parentid, 'text': text})
    assert comment is not None
    assert isinstance(comment, dict)
    assert len(comment) == 7
    assert 'commentid' in comment
    assert isinstance(comment['commentid'], int)
    assert comment['commentid'] != 0
    comment2 = get_comment(conn, comment['commentid'])
    assert comment2 is not None
    assert comment2['text'] == text
    assert comment2['deleted'] is False
    assert (comment2['datetime'] - dt).seconds < 1
    remove_comment(conn, comment['commentid'])


# noinspection PyShadowingNames
def test_remove_comment(conn):
    userid = random.choice(get_users(conn))['userid']
    parentid = random.choice(get_comments(conn)[1])['entityid']
    text = g.text.text(quantity=random.randrange(1, 3))
    comment1 = new_comment(conn, {'userid': userid, 'parentid': parentid, 'text': text})
    comment2 = get_comment(conn, comment1['commentid'])
    cnt = remove_comment(conn, comment2['commentid'])
    assert cnt == 1
    comment3 = get_comment(conn, comment1['commentid'])
    assert comment3 is not None
    assert comment3['deleted'] is True


# noinspection PyShadowingNames
def test_remove_wrong_comment(conn):
    cnt = remove_comment(conn, 0)
    assert cnt == 0


# noinspection PyShadowingNames
def test_update_comment(conn):
    userid = random.choice(get_users(conn))['userid']
    parentid = random.choice(get_comments(conn)[1])['entityid']
    text2 = text1 = g.text.text(quantity=random.randrange(1, 3))
    comment1 = new_comment(conn, {'userid': userid, 'parentid': parentid, 'text': text1})
    assert comment1 is not None
    comment2 = get_comment(conn, comment1['commentid'])
    assert comment2 is not None
    assert comment2['text'] == text1
    while text2 == text1:
        text2 = g.text.text(quantity=random.randrange(1, 3))
    res = update_comment(conn, comment1['commentid'], {'text': text2})
    assert res is not None
    assert res == 1
    comment3 = get_comment(conn, comment1['commentid'])
    assert comment3 is not None
    assert comment3['commentid'] == comment1['commentid']
    assert comment3['entityid'] == comment1['entityid']
    assert comment3['userid'] == comment1['userid']
    assert comment3['parentid'] == comment1['parentid']
    assert comment3['datetime'] == comment1['datetime']
    assert comment3['deleted'] == comment1['deleted']
    assert comment3['text'] != comment1['text']
    assert comment3['text'] == text2
    remove_comment(conn, comment1['commentid'])
