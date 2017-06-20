from typing import NamedTuple

User = NamedTuple('User', [('entityid', int), ('userid', int), ('name', str)])


def get_users(conn):
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users;")
    # noinspection PyProtectedMember,PyCallingNonCallable
    users = [dict(User(*rec)._asdict()) for rec in cur.fetchall()]
    return users
