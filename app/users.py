from typing import NamedTuple, List, Dict, Any, Optional

User = NamedTuple('User', [('entityid', int), ('userid', int), ('name', str)])


def get_users(conn) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users;")
    # noinspection PyProtectedMember,PyCallingNonCallable
    users = [dict(User(*rec)._asdict()) for rec in cur.fetchall()]
    cur.close()
    return users


def get_user(conn, user_id: int) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users WHERE userid=%s;", [user_id])
    # noinspection PyProtectedMember,PyCallingNonCallable
    users = [dict(User(*rec)._asdict()) for rec in cur.fetchall()]
    cur.close()
    if users is None or len(users) < 1:
        return None
    return users[0]


def new_user(conn, data):
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (%s) RETURNING userid, entityid", [data['name']])
        (user_id, entity_id) = cur.fetchone()
        conn.commit()
        cur.close()
    except:
        raise
    # noinspection PyCallingNonCallable,PyProtectedMember
    return dict(User(entity_id, user_id, data['name'])._asdict())


def remove_user(conn, user_id: int) -> int:
    # TODO: Проверять контент юзера
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE userid=%s;", [user_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except:
        raise
    return cnt
