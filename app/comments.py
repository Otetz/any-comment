import datetime
from typing import NamedTuple, List, Dict, Any, Optional, Tuple


class Comment(NamedTuple('Comment',
                         [('entityid', int), ('commentid', int), ('userid', int), ('datetime', datetime.datetime),
                          ('parentid', int), ('text', str), ('deleted', bool)])):
    """
    Комментарий.

    Аттрибуты:
        - entityid (int) — Идентификатор сущности комментария (сквозной по всем объектам)
        - commentid (int) — Идентификатор комментария
        - userid (int) — Идентификатор пользователя-автора
        - datetime (datetime.datetime) – Дата создания комментария
        - parentid (int) – Идентификатор родительской сущности
        - text (str) — Текст комментария
        - deleted (bool) – Флаг удалённого комментария
    """

    data_fields = ['userid', 'datetime', 'parentid', 'text', 'deleted']
    """Поля **данных** комментария (например, необходимые для добавления нового)."""

    @property
    def dict(self):
        """Возвращает поля в виде обычного словаря."""
        return dict(self._asdict())


def get_comments(conn, offset: int = 0, limit: int = 100) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Получение всех *Комментариев* (:class:`app.comments.Comment`).

    :param conn: Psycopg2 соединение
    :param offset:
    :param limit:
    :return: Список комментариев
    :rtype: list
    """
    cur = conn.cursor()
    # В лоб считать неудалённые записи нельзя - будет FullScan, потому немного хитрим:
    # Берем количество записей из таблицы статистики и вычитаем число удалённых записей.
    # Обе операции делаются по индексам и потому максимально быстрые.
    cur.execute("SELECT (SELECT n_live_tup FROM pg_stat_all_tables WHERE relname = 'comments') "
                "- "
                "(SELECT COUNT(deleted) FROM comments WHERE deleted = TRUE);", [False])
    total = cur.fetchone()[0]

    cur.execute("SELECT entityid, commentid, userid, datetime, parentid, text, deleted "
                "FROM comments "
                "WHERE deleted = %s "
                "LIMIT %s OFFSET %s;", [False, limit, offset])
    comments = [Comment(*rec).dict for rec in cur.fetchall()]
    cur.close()
    return total, comments


def get_comment(conn, comment_id: int) -> Optional[Dict[str, Any]]:
    """
    Получение конкретного *Комментария* (:class:`app.comments.Comment`).

    :param conn: Psycopg2 соединение
    :param int comment_id: Идентификатор комментария
    :return: Комментарий (словарь всех полей)
    :rtype: dict
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT entityid, commentid, userid, datetime, parentid, text, deleted FROM comments WHERE commentid = %s;",
        [comment_id])
    comments = [Comment(*rec) for rec in cur.fetchall()]
    cur.close()
    if comments is None or len(comments) < 1:
        return None
    return comments[0].dict


def new_comment(conn, data) -> Dict[str, Any]:
    """
    Сохранение нового *Комментария* (:class:`app.comments.Comment`).

    Следующие поля данных могут быть опущены при создании:
        - datetime (datetime.datetime) — Дата создания комментария, по умолчанию — текущий момент времени
        - deleted (bool) — Флаг удалённого комментария, по умолчанию — False

    :param conn: Psycopg2 соединение
    :param dict data: Данные о комментарии
    :return: Комментарий (словарь всех полей)
    :rtype: dict
    """
    data['deleted'] = data.get('deleted', False)
    data['datetime'] = data.get('datetime', datetime.datetime.now())
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO comments (userid, datetime, parentid, text, deleted) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING commentid, entityid",
                    [data['userid'], data['datetime'], data['parentid'], data['text'], data['deleted']])
        (comment_id, entity_id) = cur.fetchone()
        conn.commit()
        cur.close()
    except:
        raise
    # noinspection PyArgumentList
    return Comment(entity_id, comment_id, data['userid'], data['datetime'], data['parentid'], data['text'],
                   data['deleted']).dict


def remove_comment(conn, comment_id: int) -> Optional[int]:
    """
    Удаление *Комментария* (:class:`app.comments.Comment`).

    Комментарию устанавливается флаг удалённого.

    :param conn: Psycopg2 соединение
    :param int comment_id: Идентификатор комментария
    :return: Количество удалённых записей либо None если удаление не удалось (имеются родители)
    :rtype: int
    """
    # Проверяем что удаляем лист, а не ветвь
    comment = get_comment(conn, comment_id)
    if comment is None:
        return 0
    if comment['deleted']:
        return 1  # TODO: Можно обсудить что здесь возвращать (при попытке повторного удаления).
    cur = conn.cursor()
    cur.execute("SELECT COUNT(entityid) FROM comments WHERE parentid = %s AND deleted = %s;",
                [comment['entityid'], False])
    cnt = cur.fetchone()[0]
    cur.close()
    if cnt != 0:
        return None

    data = {name: comment[name] for name in Comment.data_fields}
    data['deleted'] = True
    try:
        cnt = update_comment(conn, comment_id, data=data)
    except:
        raise
    return cnt


def update_comment(conn, comment_id: int, data: Dict[str, Any]) -> int:
    """
    Обновление информации о *Комментарии* (:class:`app.comments.Comment`).

    :param conn: Psycopg2 соединение
    :param int comment_id: Идентификатор комментария
    :param dict data: Данные о Комментарии
    :return: Количество обновлённых записей
    :rtype: int
    """
    comment = get_comment(conn, comment_id)
    if comment is None:
        return 0
    # Формируем полный словарь данных, для отсутствующих значений используем данные из базы
    data = {x: data.get(x, comment[x]) for x in Comment.data_fields}
    try:
        cur = conn.cursor()
        cur.execute("UPDATE comments SET userid = %s, datetime = %s, parentid= %s, text = %s, deleted = %s "
                    "WHERE commentid = %s",
                    [data['userid'], data['datetime'], data['parentid'], data['text'], data['deleted'],
                     comment_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except:
        raise
    return cnt
