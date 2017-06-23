import datetime
import random

from flaky import flaky

from app.comments import first_level_comments as comments_first_level_comments
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


@flaky
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
    for c in comments:
        assert c['parentid'] == comment['entityid']
