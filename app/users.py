from typing import NamedTuple, List, Dict, Any

User = NamedTuple('User', [('entityid', int), ('userid', int), ('name', str)])


def get_users(conn) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users;")
    # noinspection PyProtectedMember,PyCallingNonCallable
    users = [dict(User(*rec)._asdict()) for rec in cur.fetchall()]
    return users
