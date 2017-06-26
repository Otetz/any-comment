import csv
import datetime
import random
from io import StringIO
from urllib.parse import urlparse

import dateutil.parser
import xmltodict
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
        check_record(res.json['response'])


def check_record(record):
    assert record is not None
    assert isinstance(record, dict)
    assert len(record) == 7
    for name in ['entityid', 'commentid'] + Comment.data_fields:
        if name == 'userid':
            continue
        assert name in record
    assert isinstance(record['author'], dict)
    assert len(record['author']) == 2
    assert 'userid' in record['author']
    assert isinstance(record['author']['userid'], int)
    assert record['author']['userid'] > 0
    assert 'name' in record['author']
    assert isinstance(record['author']['name'], str)
    assert record['author']['name'] != ''
    assert dateutil.parser.parse(record['datetime'])


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
        check_record(random.choice(res.json))


@flaky(max_runs=10, min_passes=1)
def test_get_descendants_attach_json(app, client):
    with app.app_context():
        comment = random.choice(get_comments(db_conn())[1])
        res = client.get(url_for('comments.get_descendants', comment_id=comment['commentid'], fmt='json'))
        assert res is not None
        assert res.status_code == 200
        assert res.json is not None
        assert len(res.json) >= 1
        check_record(random.choice(res.json))


def parse_csv_comment(rec):
    if 'author_userid' not in rec or 'author_name' not in rec:
        return rec
    rec['author'] = {'userid': rec['author_userid'], 'name': rec['author_name']}
    for n in ['author_userid', 'author_name']:
        del rec[n]
    return parse_comment_types(rec)


@flaky(max_runs=10, min_passes=1)
def test_get_descendants_attach_csv(app, client):
    with app.app_context():
        comment = random.choice(get_comments(db_conn())[1])
        res = client.get(url_for('comments.get_descendants', comment_id=comment['commentid'], fmt='csv'))
        assert res is not None
        assert res.status_code == 200
        assert res.data is not None
        records = []
        with StringIO(str(res.data, encoding='windows-1251')) as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                records.append(row)
        assert len(records) >= 1
        check_record(parse_csv_comment(random.choice(records)))


def parse_comment_types(rec):
    rec['author']['userid'] = int(rec['author']['userid'])
    for n in ['entityid', 'commentid', 'parentid']:
        rec[n] = int(rec[n])
    for n in ['deleted']:
        rec[n] = bool(rec[n])
    return rec


def parse_xml_comment(rec):
    rec['author'] = dict(rec['author'])
    return parse_comment_types(rec)


@flaky(max_runs=10, min_passes=1)
def test_get_descendants_attach_xml(app, client):
    with app.app_context():
        comment = random.choice(get_comments(db_conn())[1])
        res = client.get(url_for('comments.get_descendants', comment_id=comment['commentid'], fmt='xml'))
        assert res is not None
        assert res.status_code == 200
        assert res.data is not None
        xml_resp = dict(xmltodict.parse(str(res.data, encoding='utf-8')))
        assert len(xml_resp['response']['record']) >= 1
        xml_rec = dict(random.choice(list(xml_resp['response']['record'])))
        check_record(parse_xml_comment(xml_rec))
