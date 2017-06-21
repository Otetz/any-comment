from typing import NamedTuple, List, Dict, Any, Optional


class User(NamedTuple('User', [('entityid', int), ('userid', int), ('name', str)])):
    """
    Пользователь.

    Аттрибуты:
        - entityid (int) — Идентификатор сущности пользователя (сквозной по всем объектам)
        - userid (int) — Идентификатор пользователя
        - name (str) — Имя пользователя
    """

    data_fields = ['name']
    """Поля **данных** пользователя (например, необходимые для добавления нового)."""

    @property
    def dict(self):
        """Возвращает поля в виде обычного словаря."""
        return dict(self._asdict())


def get_users(conn) -> List[Dict[str, Any]]:
    """
    Получение всех *Пользователей* (:class:`app.users.User`).

    :param conn: Psycopg2 соединение
    :return: Список пользователей
    :rtype: list
    """
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users;")
    users = [User(*rec).dict for rec in cur.fetchall()]
    cur.close()
    return users


def get_user(conn, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получение конкретного *Пользователя* (:class:`app.users.User`).

    :param conn: Psycopg2 соединение
    :param int user_id: Идентификатор пользователя
    :return: Пользователь (словарь всех полей)
    :rtype: dict
    """
    cur = conn.cursor()
    cur.execute("SELECT entityid, userid, name FROM users WHERE userid = %s;", [user_id])
    users = [User(*rec) for rec in cur.fetchall()]
    cur.close()
    if users is None or len(users) < 1:
        return None
    return users[0].dict


def new_user(conn, data) -> Dict[str, Any]:
    """
    Сохранение нового *Пользователя* (:class:`app.users.User`).

    :param conn: Psycopg2 соединение
    :param dict data: Данные о пользователе
    :return: Пользователь (словарь всех полей)
    :rtype: dict
    """
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (%s) RETURNING userid, entityid", [data['name']])
        (user_id, entity_id) = cur.fetchone()
        conn.commit()
        cur.close()
    except:
        raise
    # noinspection PyArgumentList
    return User(entity_id, user_id, data['name']).dict


def remove_user(conn, user_id: int) -> int:
    """
    Удаление *Пользователя* (:class:`app.users.User`).

    :param conn: Psycopg2 соединение
    :param int user_id: Идентификатор пользователя
    :return: Количество удалённых записей
    :rtype: int
    """
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
    """
    Обновление информации о *Пользователе* (:class:`app.users.User`).

    :param conn: Psycopg2 соединение
    :param int user_id: Идентификатор пользователя
    :param dict data: Данные о пользователе
    :return: Количество обновлённых записей
    :rtype: int
    """
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET name = %s WHERE userid = %s", [data['name'], user_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except:
        raise
    return cnt
