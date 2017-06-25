import datetime
import random

from dateutil.tz import tzlocal
from elizabeth import Generic
from flaky import flaky

from app.comments import get_comments, get_comment, new_comment, remove_comment, update_comment, descendants
from app.users import get_users

g = Generic('ru')


def test_get_comments(conn):
    comments = get_comments(conn)[1]
    assert comments is not None
    assert isinstance(comments, list)
    assert len(comments) > 0
    assert comments[0] is not None
    assert isinstance(comments[0], dict)
    assert len(comments[0]) == 7
    for field in ['entityid', 'commentid', 'parentid']:
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
    assert 'author' in comments[0]
    assert isinstance(comments[0]['author'], dict)
    assert len(comments[0]['author']) == 2
    assert 'userid' in comments[0]['author']
    assert isinstance(comments[0]['author']['userid'], int)
    assert comments[0]['author']['userid'] > 0
    assert 'name' in comments[0]['author']
    assert isinstance(comments[0]['author']['name'], str)
    assert comments[0]['author']['name'] != ''


def test_get_comment(conn):
    comment = random.choice(get_comments(conn)[1])
    assert comment is not None
    assert isinstance(comment, dict)
    assert len(comment) == 7
    assert 'text' in comment
    assert isinstance(comment['text'], str)
    assert comment['text'] != ''


def test_get_comment_error(conn):
    comment = get_comment(conn, 0)
    assert comment is None


def test_new_comment(conn):
    userid = random.choice(get_users(conn)[1])['userid']
    parentid = random.choice(get_comments(conn)[1])['entityid']
    text = g.text.text(quantity=random.randrange(1, 3))
    dt = datetime.datetime.now(tz=tzlocal())
    comment_id = new_comment(conn, {'userid': userid, 'parentid': parentid, 'text': text})[0]
    comment = get_comment(conn, comment_id)
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


def test_remove_comment(conn):
    userid = random.choice(get_users(conn)[1])['userid']
    parentid = random.choice(get_comments(conn)[1])['entityid']
    text = g.text.text(quantity=random.randrange(1, 3))
    comment1_id = new_comment(conn, {'userid': userid, 'parentid': parentid, 'text': text})[0]
    comment1 = get_comment(conn, comment1_id)
    assert comment1 is not None
    cnt = remove_comment(conn, comment1_id)
    assert cnt == 1
    comment3 = get_comment(conn, comment1_id)
    assert comment3 is not None
    assert comment3['deleted'] is True


def test_remove_wrong_comment(conn):
    cnt = remove_comment(conn, 0)
    assert cnt == 0


def test_update_comment(conn):
    userid = random.choice(get_users(conn)[1])['userid']
    parentid = random.choice(get_comments(conn)[1])['entityid']
    text2 = text1 = g.text.text(quantity=random.randrange(1, 3))
    comment1_id = new_comment(conn, {'userid': userid, 'parentid': parentid, 'text': text1})[0]
    assert comment1_id is not None
    comment2 = get_comment(conn, comment1_id)
    assert comment2 is not None
    assert comment2['text'] == text1
    while text2 == text1:
        text2 = g.text.text(quantity=random.randrange(1, 3))
    res = update_comment(conn, comment1_id, {'text': text2})
    assert res is not None
    assert res == 1
    comment3 = get_comment(conn, comment2['commentid'])
    assert comment3 is not None
    assert comment3['commentid'] == comment2['commentid']
    assert comment3['entityid'] == comment2['entityid']
    assert comment3['author'] == comment2['author']
    assert comment3['parentid'] == comment2['parentid']
    assert (comment3['datetime'] - comment2['datetime']).seconds < 1
    assert comment3['deleted'] == comment2['deleted']
    assert comment3['text'] != comment2['text']
    assert comment3['text'] == text2
    remove_comment(conn, comment2['commentid'])


@flaky(max_runs=10, min_passes=1)
def test_descendants(conn):
    comment = random.choice(get_comments(conn)[1])
    i = 0
    for rec in descendants(conn, comment['commentid']):
        assert isinstance(rec, dict)
        assert len(rec) == 7
        i += 1
        if i > 10:
            break
