from typing import NamedTuple, List, Dict, Any, Optional


class User(NamedTuple('User', [('entityid', int), ('userid', int), ('name', str)])):
    """Пользователь."""

    data_fields = ['name']

    @property
    def dict(self):
        """Возвращает поля в обычном словаре"""
        return dict(self._asdict())


def get_users(conn) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users;")
    users = [User(*rec).dict for rec in cur.fetchall()]
    cur.close()
    return users


def get_user(conn, user_id: int) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users WHERE userid = %s;", [user_id])
    users = [User(*rec) for rec in cur.fetchall()]
    cur.close()
    if users is None or len(users) < 1:
        return None
    return users[0].dict


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
    return User(entity_id, user_id, data['name']).dict


def remove_user(conn, user_id: int) -> int:
    # TODO: Проверять контент юзера
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE userid = %s;", [user_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except:
        raise
    return cnt


def update_user(conn, user_id: int, data: Dict[str, Any]) -> int:
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET name = %s WHERE userid = %s", [data['name'], user_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except:
        raise
    return cnt
