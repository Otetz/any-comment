from app.users import get_users


def test_pagination(conn):
    total, users = get_users(conn)
    assert total == len(users)
    total2, users2 = get_users(conn, offset=5, limit=5)
    assert total2 == total
    assert len(users2) == 5
    assert users2[0] == users[5]
    assert users2[-1] == users[9]
