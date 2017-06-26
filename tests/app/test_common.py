import datetime
import random

from flaky import flaky

from app.comments import first_level_comments as comments_first_level_comments
from app.common import entity_descendants
from app.posts import get_posts, first_level_comments as post_first_level_comments
from app.users import get_users


def test_pagination(conn):
    total, users = get_users(conn)
    assert total == len(users)
    total2, users2 = get_users(conn, offset=5, limit=5)
    assert total2 == total
    assert len(users2) == 5
    assert users2[0] == users[5]
    assert users2[-1] == users[9]


@flaky(max_runs=10, min_passes=1)
def test_first_level_comments(conn):
    posts = get_posts(conn)[1]
    comments = []
    while not comments:
        post = random.choice(posts)
        comments = post_first_level_comments(conn, post['postid'])[1]
    comment = random.choice(comments)
    total, comments = comments_first_level_comments(conn, comment['commentid'])
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
    assert isinstance(comments[0]['author'], dict)
    assert len(comments[0]['author']) == 2
    assert 'userid' in comments[0]['author']
    assert isinstance(comments[0]['author']['userid'], int)
    assert comments[0]['author']['userid'] > 0
    assert 'name' in comments[0]['author']
    assert isinstance(comments[0]['author']['name'], str)
    assert comments[0]['author']['name'] != ''
    for c in comments:
        assert c['parentid'] == comment['entityid']


@flaky(max_runs=20, min_passes=1)
def test_entity_descendants(conn):
    posts = get_posts(conn)[1]
    post = random.choice(posts)
    i = 0
    for rec in entity_descendants(conn, post['entityid']):
        assert isinstance(rec, dict)
        assert len(rec) == 7
        i += 1
        if i > 10:
            break
    assert i != 0
