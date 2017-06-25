import datetime
import json
from typing import Dict, Any, Tuple, List, Iterator

import flask
import psycopg2
from flask import current_app as app, request
from psycopg2.extras import RealDictCursor


# region Exceptions
class AnyCommentException(Exception):
    pass


class DatabaseException(AnyCommentException):
    pass


class InvalidArgumentsException(AnyCommentException):
    pass


# endregion

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def db_conn():
    return psycopg2.connect(app.config['DB_URI'])


def json_kwargs() -> Dict[str, Any]:
    return {
        'ensure_ascii': app.config['JSON_ENSURE_ASCII'],
        'indent': app.config['JSON_INDENT']
    }


def to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, cls=DateTimeEncoder, **json_kwargs()) + "\n"


def to_json_stream(it: Iterator) -> Iterator:
    yield "[\n"
    first = True
    for rec in it:
        msg = to_json(rec)
        if not first:
            msg = ',\n' + msg
        yield msg
        first = False
    yield "]\n"


def resp(code, data: Dict[str, Any]):
    return flask.Response(status=code, mimetype="application/json; encoding=utf-8", response=to_json(data))


def affected_num_to_code(cnt: int, code: int = 404) -> int:
    return (cnt is None or cnt == 0) and code or 200


def pagination() -> (int, int):
    """
    Определение параметров пагинации из Query String запроса.

    Параметры:
        - page (int) — Опеределяет номер страницы резльтатов, по умолчанию 1
        - per_page (int) — Определяет количество результатов на одной странице, по умолчанию 10. \
          Максимальное значение 100
        - offset (int) — Начало отсчета для страницы, вычисляемое, если определено в запросе то page (номер страницы) \
          игнорируется
    :return: значения OFFSET и LIMIT для SQL-запроса
    :rtype: tuple
    """
    defaults = {'page': 1, 'per_page': 10, 'max_per_page': 100}
    args = request.args.to_dict()
    page = int(args.get('page', defaults['page']))
    per_page = min(int(args.get('per_page', defaults['per_page'])), defaults['max_per_page'])
    offset = int(args.get('offset', per_page * (page - 1)))
    return offset, per_page


def entity_first_level_comments(conn, entityid: int, offset: int = 0, limit: int = 100) -> \
        Tuple[int, List[Dict[str, Any]]]:
    """
    Показать комментарии первого уровня вложенности к указанной сущности в порядке возрастания даты создания
    комментария.

    Поддерживается пагинация :func:`app.common.pagination`.

    :param conn: Psycopg2 соединение
    :param int entityid: Идентификатор родительской сущности
    :param int offset: Начало отсчета, по умолчанию 0
    :param int limit: Количество результатов, по умолчанию максимум = 100
    :return: Общее количество и Список комментариев первого уровня вложенности
    :rtype: tuple
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(entityid) FROM comments WHERE parentid = %s AND deleted = %s;", [entityid, False])
    total = cur.fetchone()['count']
    cur.execute("SET timezone = 'Europe/Moscow';")
    cur.execute("SELECT C.entityid, C.commentid, C.userid, C.datetime, C.parentid, C.text, C.deleted, U.name "
                "FROM comments AS C "
                "LEFT JOIN users AS U ON U.userid = C.userid "
                "WHERE parentid = %s AND deleted = %s "
                "ORDER BY C.datetime ASC "
                "LIMIT %s OFFSET %s;", [entityid, False, limit, offset])
    comments = []
    for rec in cur.fetchall():
        rec['author'] = {'userid': rec.pop('userid'), 'name': rec.pop('name')}
        comments.append(rec)
    cur.close()
    return total, comments


def entity_descendants(conn, entity_id: int, batch_size: int = 50) -> Iterator:
    """
    Все дочерние комментарии для указанной сущности.

    :param conn: Psycopg2 соединение
    :param entity_id: Идентификатор родительской сущности
    :param batch_size: Размер курсора, по умолчанию 50
    :return: Итератор всех дочерних комментариев
    :rtype: iterator
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.itersize = batch_size
    cur.execute("SET timezone = 'Europe/Moscow';")
    # noinspection SqlResolve
    cur.execute("SELECT C.entityid, C.commentid, C.userid, C.datetime, C.parentid, C.text, C.deleted, U.name "
                "FROM comments_tree(%s) AS C "
                "LEFT JOIN users AS U ON U.userid = C.userid "
                "WHERE C.deleted = FALSE;", [entity_id])
    for rec in cur:
        rec['author'] = {'userid': rec.pop('userid'), 'name': rec.pop('name')}
        yield rec
    cur.close()
    conn.commit()
