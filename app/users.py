from typing import NamedTuple, List, Dict, Any, Optional, Tuple

import psycopg2

from app.common import DatabaseException


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


def get_users(conn, offset: int = 0, limit: int = 100) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Получение всех *Пользователей* (:class:`app.users.User`).

    :param conn: Psycopg2 соединение
    :param int offset: Начало отсчета, по умолчанию 0
    :param int limit: Количество результатов, по умолчанию максимум = 100
    :return: Список пользователей
    :rtype: list
    """
    cur = conn.cursor()
    cur.execute("SELECT COUNT(userid) FROM users;")
    total = cur.fetchone()[0]

    cur.execute("SELECT entityid, userid, name FROM users LIMIT %s OFFSET %s;", [limit, offset])
    users = [User(*rec).dict for rec in cur.fetchall()]
    cur.close()
    return total, users


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
    except psycopg2.DatabaseError as e:
        raise DatabaseException(e)
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
    except psycopg2.DatabaseError as e:
        raise DatabaseException(e)
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
    except psycopg2.DatabaseError as e:
        raise DatabaseException(e)
    return cnt
