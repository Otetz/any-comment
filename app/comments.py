import datetime
from typing import List, Dict, Any, Optional, Tuple, Iterator

import psycopg2
from dateutil.tz import tzlocal
from psycopg2.extras import RealDictCursor

from app.common import DatabaseException, entity_first_level_comments, entity_descendants
from app.types import Comment


def get_comments(conn, offset: int = 0, limit: int = 100) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Получение всех *Комментариев* (:class:`app.comments.Comment`).

    :param conn: Psycopg2 соединение
    :param int offset: Начало отсчета, по умолчанию 0
    :param int limit: Количество результатов, по умолчанию максимум = 100
    :return: Общее количество и Список комментариев
    :rtype: tuple
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SET timezone = 'Europe/Moscow';")
    # В лоб считать неудалённые записи нельзя - будет FullScan, потому немного хитрим:
    # Берем количество записей из таблицы статистики и вычитаем число удалённых записей.
    # Обе операции делаются по индексам и потому максимально быстрые.
    cur.execute("SELECT (SELECT n_live_tup FROM pg_stat_all_tables WHERE relname = 'comments') "
                "- "
                "(SELECT COUNT(deleted) FROM comments WHERE deleted = %s) AS count;", [True])
    total = cur.fetchone()['count']

    cur.execute("SELECT C.entityid, C.commentid, C.userid, C.datetime, C.parentid, C.text, C.deleted, U.name "
                "FROM comments AS C "
                "LEFT JOIN users AS U ON U.userid = C.userid "
                "WHERE C.deleted = %s "
                "LIMIT %s OFFSET %s;", [False, limit, offset])
    comments = []
    for rec in cur.fetchall():
        rec['author'] = {'userid': rec.pop('userid'), 'name': rec.pop('name')}
        comments.append(rec)
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
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SET timezone = 'Europe/Moscow';")
    cur.execute("SELECT C.entityid, C.commentid, C.userid, C.datetime, C.parentid, C.text, C.deleted, U.name "
                "FROM comments AS C "
                "LEFT JOIN users AS U ON U.userid = C.userid "
                "WHERE C.commentid = %s;",
                [comment_id])
    rec = cur.fetchone()
    if not rec:
        return None
    rec['author'] = {'userid': rec.pop('userid'), 'name': rec.pop('name')}
    cur.close()
    return rec


def new_comment(conn, data) -> Tuple[int, int]:
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
    data['datetime'] = data.get('datetime', datetime.datetime.now(tz=tzlocal()))
    try:
        cur = conn.cursor()
        cur.execute("SET timezone = 'Europe/Moscow';")
        cur.execute("INSERT INTO comments (userid, datetime, parentid, text, deleted) "
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING commentid, entityid",
                    [data['userid'], data['datetime'], data['parentid'], data['text'], data['deleted']])
        (comment_id, entity_id) = cur.fetchone()
        conn.commit()
        cur.close()
    except psycopg2.DatabaseError as e:
        raise DatabaseException(e)
    return comment_id, entity_id


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
    if comment is None or comment['deleted']:
        return 0

    cur = conn.cursor()
    cur.execute("SELECT COUNT(entityid) FROM comments WHERE parentid = %s AND deleted = %s;",
                [comment['entityid'], False])
    cnt = cur.fetchone()[0]
    cur.close()
    if cnt != 0:
        return None

    comment['userid'] = comment['author']['userid']
    data = {name: comment[name] for name in Comment.data_fields}
    data['deleted'] = True
    try:
        cnt = update_comment(conn, comment_id, data=data)
    except psycopg2.DatabaseError as e:
        raise DatabaseException(e)
    return cnt


def update_comment(conn, comment_id: int, data: Dict[str, Any]) -> int:
    """
    Обновление информации о *Комментарии* (:class:`app.comments.Comment`).

    Если какие-то из полей данных не заполнены, то будут использованы текущие значения из БД.

    :param conn: Psycopg2 соединение
    :param int comment_id: Идентификатор комментария
    :param dict data: Данные о Комментарии
    :return: Количество обновлённых записей
    :rtype: int
    """
    comment = get_comment(conn, comment_id)
    if comment is None or comment['deleted']:
        return 0
    comment['userid'] = comment['author']['userid']
    # Формируем полный словарь данных, для отсутствующих значений используем данные из базы
    data = {x: data.get(x, comment[x]) for x in Comment.data_fields}
    if data == comment:
        return 0
    try:
        cur = conn.cursor()
        cur.execute("SET timezone = 'Europe/Moscow';")
        # TODO: Обновлять только реально изменившиеся поля
        cur.execute("UPDATE comments SET userid = %s, datetime = %s, parentid= %s, text = %s, deleted = %s "
                    "WHERE commentid = %s",
                    [data['userid'], data['datetime'], data['parentid'], data['text'], data['deleted'],
                     comment_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except psycopg2.DatabaseError as e:
        raise DatabaseException(e)
    return cnt


def first_level_comments(conn, comment_id: int, offset: int = 0, limit: int = 100) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Показать комментарии первого уровня вложенности к указанному комментарию.

    Поддерживается пагинация :func:`app.common.pagination`.

    :param conn: Psycopg2 соединение
    :param int comment_id: Идентификатор родительского комментария
    :param int offset: Начало отсчета, по умолчанию 0
    :param int limit: Количество результатов, по умолчанию максимум = 100
    :return: Общее количество и Список комментариев первого уровня вложенности
    :rtype: tuple
    """
    comment = get_comment(conn, comment_id)
    if comment is None:
        return 0, []
    return entity_first_level_comments(conn, comment['entityid'], offset, limit)


def descendants(conn, comment_id: int) -> Iterator:
    """
    Все дочерние комментарии для указанного родительского.

    :param conn: Psycopg2 соединение
    :param comment_id: Идентификатор родительского комментария
    :return: Итератор всех дочерних комментариев
    :rtype: iterator
    """
    comment = get_comment(conn, comment_id)
    if comment is None:
        raise StopIteration
    return entity_descendants(conn, comment['entityid'])
